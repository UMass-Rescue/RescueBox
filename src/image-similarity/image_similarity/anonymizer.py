"""
Privacy-preserving image anonymization using SAM3 segmentation (ONNX).

Detects specified visual concepts (faces, text, logos, etc.) in an image using
Facebook's SAM3 model via ONNX Runtime, then blacks out those regions so that
downstream embeddings never encode sensitive content.

Anonymization approach inspired by:
    Bissias, Bagdasarian & Levine, "Contrastive Privacy: A Semantic Approach
    to Measuring Privacy of AI-based Sanitization" (2026).
"""

from __future__ import annotations

import logging
from typing import Optional, Sequence

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

DEFAULT_TARGET_LABELS: list[str] = ["face", "person", "text", "sign", "logo"]
DEFAULT_THRESHOLD = 0.6
_SAM3_HF_REPO = "vietanhdev/segment-anything-3-onnx-models"
_SAM3_FILES = {
    "encoder": "sam3_image_encoder.onnx",
    "decoder": "sam3_decoder.onnx",
    "language": "sam3_language_encoder.onnx",
}

_cached_sam3 = None


def _download_sam3_onnx() -> dict[str, str]:
    """Download SAM3 ONNX models from HuggingFace Hub, returning cached paths."""
    from huggingface_hub import hf_hub_download

    paths = {}
    for key, filename in _SAM3_FILES.items():
        paths[key] = hf_hub_download(repo_id=_SAM3_HF_REPO, filename=filename)
        data_file = filename + ".data"
        try:
            hf_hub_download(repo_id=_SAM3_HF_REPO, filename=data_file)
        except Exception:
            pass  # .data file may not exist for smaller models
    return paths


def _load_sam3():
    """Load SAM3 ONNX model and cache for reuse across images."""
    global _cached_sam3
    if _cached_sam3 is not None:
        return _cached_sam3

    from samexporter.sam3_onnx import SegmentAnything3ONNX

    logger.info("Downloading/loading SAM3 ONNX models from %s", _SAM3_HF_REPO)
    paths = _download_sam3_onnx()

    model = SegmentAnything3ONNX(
        image_encoder_path=paths["encoder"],
        decoder_model_path=paths["decoder"],
        language_encoder_path=paths["language"],
    )
    _cached_sam3 = model
    logger.info("SAM3 ONNX model loaded and cached.")
    return _cached_sam3


def _create_mask(
    image: Image.Image,
    labels: Sequence[str],
    threshold: float = DEFAULT_THRESHOLD,
) -> np.ndarray:
    """Segment *labels* in *image* via SAM3 ONNX and return a binary mask.

    Each label is processed independently and the per-label masks are merged
    (logical OR). Non-zero pixels in the returned mask mark detected regions.
    """
    model = _load_sam3()
    img_array = np.array(image)[:, :, ::-1]  # PIL RGB -> BGR for samexporter

    h, w = image.size[1], image.size[0]
    combined = np.zeros((h, w), dtype=np.uint8)

    for label in labels:
        try:
            embedding = model.encode(img_array, text_prompt=label)
            masks = model.predict_masks(embedding, prompt=[], threshold=threshold)

            for mask in masks:
                mask_uint8 = (mask.astype(np.uint8)) * 255
                if mask_uint8.shape != combined.shape:
                    from PIL import Image as _Img
                    mask_uint8 = np.array(
                        _Img.fromarray(mask_uint8).resize((w, h), Image.Resampling.NEAREST)
                    )
                combined = np.maximum(combined, mask_uint8)

            logger.info("SAM3 '%s': %d region(s) detected", label, len(masks))
        except Exception as exc:
            logger.warning("SAM3 segmentation failed for label '%s': %s", label, exc)

    return combined


def _apply_blackout(image: Image.Image, mask: np.ndarray) -> Image.Image:
    """Replace masked regions with black pixels."""
    result = np.array(image).copy()
    result[mask > 127] = 0
    return Image.fromarray(result)


def anonymize_image(
    image: Image.Image,
    target_labels: Sequence[str] = DEFAULT_TARGET_LABELS,
    threshold: float = DEFAULT_THRESHOLD,
) -> Image.Image:
    """Anonymize an image by blacking out regions matching *target_labels*.

    Returns a new PIL Image with sensitive regions replaced by black pixels.
    The original image is never modified.
    """
    mask = _create_mask(image, target_labels, threshold)
    return _apply_blackout(image, mask)
