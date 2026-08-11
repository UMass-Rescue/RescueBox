"""
Privacy-preserving image anonymization using CLIPSeg text-prompted segmentation.

Detects specified visual concepts (faces, text, logos, etc.) in an image using
CLIPSeg via ONNX Runtime, then blacks out those regions so that downstream
embeddings never encode sensitive content.

Anonymization approach inspired by:
    Bissias, Bagdasarian & Levine, "Contrastive Privacy: A Semantic Approach
    to Measuring Privacy of AI-based Sanitization" (2026).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageFilter
from transformers import CLIPSegProcessor, CLIPTokenizerFast, ViTImageProcessor

logger = logging.getLogger(__name__)

DEFAULT_TARGET_LABELS: list[str] = ["face", "person", "text", "sign", "logo"]
DEFAULT_THRESHOLD = 0.3
DEFAULT_DILATE = 5
DEFAULT_BLUR = 5

_MODELS_DIR = Path(__file__).resolve().parent / "onnx_models"
_CLIPSEG_ONNX_PATH = _MODELS_DIR / "clipseg-rd64-refined.onnx"
_CLIPSEG_TOKENIZER_PATH = _MODELS_DIR / "clipseg_tokenizer.json"
_CLIPSEG_TOKENIZER_CONFIG_PATH = _MODELS_DIR / "clipseg_tokenizer_config.json"
_CLIPSEG_PREPROCESSOR_CONFIG_PATH = _MODELS_DIR / "clipseg_preprocessor_config.json"

_cached_session: Optional[ort.InferenceSession] = None
_cached_processor: Optional[CLIPSegProcessor] = None


def _sigmoid(x: np.ndarray) -> np.ndarray:
    """NumPy sigmoid function."""
    return 1.0 / (1.0 + np.exp(-x))


def _load_clipseg() -> tuple[ort.InferenceSession, CLIPSegProcessor]:
    """Load CLIPSeg ONNX session and processor, caching for reuse."""
    global _cached_session, _cached_processor
    if _cached_session is not None and _cached_processor is not None:
        return _cached_session, _cached_processor

    required_files = [
        (_CLIPSEG_ONNX_PATH, "ONNX model"),
        (_CLIPSEG_TOKENIZER_PATH, "tokenizer"),
        (_CLIPSEG_TOKENIZER_CONFIG_PATH, "tokenizer config"),
        (_CLIPSEG_PREPROCESSOR_CONFIG_PATH, "preprocessor config"),
    ]
    for path, desc in required_files:
        if not path.exists():
            raise FileNotFoundError(f"CLIPSeg {desc} not found at {path}")

    available = ort.get_available_providers()
    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    providers = [p for p in providers if p in available]
    logger.info(
        "Loading CLIPSeg ONNX model from %s (providers=%s)",
        _CLIPSEG_ONNX_PATH.name,
        providers,
    )

    _cached_session = ort.InferenceSession(str(_CLIPSEG_ONNX_PATH), providers=providers)
    tokenizer = CLIPTokenizerFast(
        vocab_file=None,
        tokenizer_file=str(_CLIPSEG_TOKENIZER_PATH),
    )
    image_processor = ViTImageProcessor.from_json_file(
        str(_CLIPSEG_PREPROCESSOR_CONFIG_PATH)
    )
    _cached_processor = CLIPSegProcessor(
        image_processor=image_processor, tokenizer=tokenizer
    )

    return _cached_session, _cached_processor


def _create_mask(
    image: Image.Image,
    labels: Sequence[str],
    threshold: float = DEFAULT_THRESHOLD,
    dilate: int = DEFAULT_DILATE,
    blur: int = DEFAULT_BLUR,
) -> Image.Image:
    """Segment *labels* in *image* via CLIPSeg ONNX and return a grayscale mask.

    All labels are processed in a single forward pass. White pixels in the
    returned mask mark detected regions.
    """
    session, processor = _load_clipseg()

    h, w = image.size[1], image.size[0]
    combined = np.zeros((h, w), dtype=np.uint8)

    inputs = processor(
        text=list(labels),
        images=[image] * len(labels),
        padding=True,
        return_tensors="np",
    )

    ort_inputs = {
        k: v for k, v in inputs.items() if k in [i.name for i in session.get_inputs()]
    }
    outputs = session.run(None, ort_inputs)

    logits = outputs[0]  # (num_labels, H, W)
    for i, label in enumerate(labels):
        mask_logits = logits[i]
        mask_prob = _sigmoid(mask_logits)
        mask_uint8 = (mask_prob * 255).astype(np.uint8)
        mask_resized = np.array(
            Image.fromarray(mask_uint8).resize((w, h), Image.Resampling.BILINEAR)
        )
        binary = (mask_resized > int(threshold * 255)).astype(np.uint8) * 255
        combined = np.maximum(combined, binary)
        detected = np.any(binary > 0)
        logger.info(
            "CLIPSeg '%s': %s", label, "detected" if detected else "not detected"
        )

    mask = Image.fromarray(combined, mode="L")

    if dilate > 0:
        for _ in range(dilate):
            mask = mask.filter(ImageFilter.MaxFilter(3))
    if blur > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=blur))

    return mask


def _apply_blackout(image: Image.Image, mask: Image.Image) -> Image.Image:
    """Replace masked regions with black pixels."""
    if mask.size != image.size:
        mask = mask.resize(image.size, Image.Resampling.LANCZOS)
    if mask.mode != "L":
        mask = mask.convert("L")
    black = Image.new("RGB", image.size, (0, 0, 0))
    return Image.composite(black, image, mask)


def anonymize_image(
    image: Image.Image,
    target_labels: Sequence[str] = DEFAULT_TARGET_LABELS,
    threshold: float = DEFAULT_THRESHOLD,
    dilate: int = DEFAULT_DILATE,
    blur: int = DEFAULT_BLUR,
) -> Image.Image:
    """Anonymize an image by blacking out regions matching *target_labels*.

    Returns a new PIL Image with sensitive regions replaced by black pixels.
    The original image is never modified.
    """
    mask = _create_mask(image, target_labels, threshold, dilate, blur)
    return _apply_blackout(image, mask)
