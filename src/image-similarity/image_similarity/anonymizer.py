"""
Privacy-preserving image anonymization using SAM3 segmentation.

Detects specified visual concepts (faces, text, logos, etc.) in an image using
Facebook's SAM3 model, then blacks out those regions so that downstream
embeddings never encode sensitive content.

Anonymization approach inspired by the contrastive-privacy framework:
    Bissias, Bagdasarian & Levine, "Contrastive Privacy: A Semantic Approach
    to Measuring Privacy of AI-based Sanitization" (2026).
    Paper:  https://arxiv.org/pdf/2605.02977.pdf
    Code:   https://github.com/umass-forensics/contrastive-privacy
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional, Sequence

import numpy as np
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)

DEFAULT_TARGET_LABELS: list[str] = ["face", "person", "text", "sign", "logo"]
DEFAULT_THRESHOLD = 0.2
DEFAULT_DILATE = 25
DEFAULT_BLUR = 5
_SAM3_MODEL_NAME = "facebook/sam3"


@dataclass
class _SAM3:
    model: Any
    processor: Any
    device: str


_cached_sam3: Optional[_SAM3] = None


def _get_device() -> str:
    import torch
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _load_sam3(device: Optional[str] = None) -> _SAM3:
    """Load SAM3 model and processor, caching for reuse across images."""
    global _cached_sam3
    if _cached_sam3 is not None:
        return _cached_sam3

    import torch
    from transformers import Sam3Model, Sam3Processor

    device = device or _get_device()
    logger.info("Loading SAM3 model: %s (device=%s)", _SAM3_MODEL_NAME, device)

    processor = Sam3Processor.from_pretrained(_SAM3_MODEL_NAME)
    if device == "cuda":
        model = Sam3Model.from_pretrained(_SAM3_MODEL_NAME, torch_dtype=torch.bfloat16)
    else:
        model = Sam3Model.from_pretrained(_SAM3_MODEL_NAME)
    model = model.to(device)

    _cached_sam3 = _SAM3(model=model, processor=processor, device=device)
    return _cached_sam3


def _create_mask(
    image: Image.Image,
    labels: Sequence[str],
    threshold: float = DEFAULT_THRESHOLD,
    dilate: int = DEFAULT_DILATE,
    blur: int = DEFAULT_BLUR,
    device: Optional[str] = None,
) -> Image.Image:
    """Segment *labels* in *image* via SAM3 and return a grayscale mask.

    Each label is processed independently and the per-label masks are merged
    (logical OR).  White pixels in the returned mask mark detected regions.
    """
    import torch

    sam3 = _load_sam3(device)
    sam3.model.eval()

    h, w = image.size[1], image.size[0]
    combined = np.zeros((h, w), dtype=np.uint8)

    for label in labels:
        try:
            inputs = sam3.processor(images=image, text=label, return_tensors="pt")
            inputs = {k: v.to(sam3.device) for k, v in inputs.items()}

            with torch.inference_mode():
                outputs = sam3.model(**inputs)

            results = sam3.processor.post_process_instance_segmentation(
                outputs,
                threshold=threshold,
                mask_threshold=0.5,
                target_sizes=inputs.get("original_sizes").tolist(),
            )[0]

            masks = results.get("masks", [])
            for mask_tensor in masks:
                object_mask = mask_tensor.cpu().numpy().astype(np.uint8) * 255
                combined = np.maximum(combined, object_mask)

            logger.info("SAM3 '%s': %d object(s) detected", label, len(masks))
        except RuntimeError as exc:
            if "CUDA out of memory" in str(exc):
                logger.warning("SAM3 OOM for '%s', skipping label", label)
            else:
                raise
        finally:
            if sam3.device == "cuda":
                torch.cuda.empty_cache()

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
