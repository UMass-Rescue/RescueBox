"""
Privacy-preserving image anonymization using CLIPSeg text-prompted segmentation.

Detects specified visual concepts (faces, text, logos, etc.) in an image using
CLIPSeg, then blacks out those regions so that downstream embeddings never
encode sensitive content.

Anonymization approach inspired by:
    Bissias, Bagdasarian & Levine, "Contrastive Privacy: A Semantic Approach
    to Measuring Privacy of AI-based Sanitization" (2026).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional, Sequence

import numpy as np
import torch
from PIL import Image, ImageFilter
from transformers import CLIPSegProcessor, CLIPSegForImageSegmentation

logger = logging.getLogger(__name__)

DEFAULT_TARGET_LABELS: list[str] = ["face", "person", "text", "sign", "logo"]
DEFAULT_THRESHOLD = 0.3
DEFAULT_DILATE = 15
DEFAULT_BLUR = 5
_CLIPSEG_MODEL_NAME = "CIDAS/clipseg-rd64-refined"


@dataclass
class _CLIPSeg:
    model: Any
    processor: Any
    device: str


_cached_clipseg: Optional[_CLIPSeg] = None


def _get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _load_clipseg(device: Optional[str] = None) -> _CLIPSeg:
    """Load CLIPSeg model and processor, caching for reuse across images."""
    global _cached_clipseg
    if _cached_clipseg is not None:
        return _cached_clipseg

    device = device or _get_device()
    logger.info("Loading CLIPSeg model: %s (device=%s)", _CLIPSEG_MODEL_NAME, device)

    processor = CLIPSegProcessor.from_pretrained(_CLIPSEG_MODEL_NAME)
    model = CLIPSegForImageSegmentation.from_pretrained(_CLIPSEG_MODEL_NAME)
    model = model.to(device)

    _cached_clipseg = _CLIPSeg(model=model, processor=processor, device=device)
    return _cached_clipseg


def _create_mask(
    image: Image.Image,
    labels: Sequence[str],
    threshold: float = DEFAULT_THRESHOLD,
    dilate: int = DEFAULT_DILATE,
    blur: int = DEFAULT_BLUR,
    device: Optional[str] = None,
) -> Image.Image:
    """Segment *labels* in *image* via CLIPSeg and return a grayscale mask.

    All labels are processed in a single forward pass. White pixels in the
    returned mask mark detected regions.
    """
    clipseg = _load_clipseg(device)
    clipseg.model.eval()

    h, w = image.size[1], image.size[0]
    combined = np.zeros((h, w), dtype=np.uint8)

    inputs = clipseg.processor(
        text=list(labels),
        images=[image] * len(labels),
        padding=True,
        return_tensors="pt",
    )
    inputs = {k: v.to(clipseg.device) for k, v in inputs.items()}

    with torch.inference_mode():
        outputs = clipseg.model(**inputs)

    logits = outputs.logits  # (num_labels, H, W)
    for i, label in enumerate(labels):
        mask_logits = logits[i]
        mask_prob = torch.sigmoid(mask_logits).cpu().numpy()
        mask_uint8 = (mask_prob * 255).astype(np.uint8)
        mask_resized = np.array(
            Image.fromarray(mask_uint8).resize((w, h), Image.Resampling.BILINEAR)
        )
        binary = (mask_resized > int(threshold * 255)).astype(np.uint8) * 255
        combined = np.maximum(combined, binary)
        detected = np.any(binary > 0)
        logger.info("CLIPSeg '%s': %s", label, "detected" if detected else "not detected")

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
    device: Optional[str] = None,
) -> Image.Image:
    """Anonymize an image by blacking out regions matching *target_labels*.

    Returns a new PIL Image with sensitive regions replaced by black pixels.
    The original image is never modified.
    """
    mask = _create_mask(image, target_labels, threshold, dilate, blur, device)
    return _apply_blackout(image, mask)
