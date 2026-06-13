"""Shared path helpers for pipeline lineage/indexing."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif")


def source_image_path_from_summary(
    summary_txt_path: str, input_dir: str
) -> Optional[str]:
    """
    Infer source image path for image-summary output files.

    Example: ``input/shot.png`` -> summary file ``shot.png.txt``.
    """
    name = Path(summary_txt_path).name
    if not name.endswith(".txt"):
        return None
    base = name[:-4]
    if not any(base.lower().endswith(ext) for ext in _IMAGE_SUFFIXES):
        return None
    candidate = str(Path(input_dir) / base)
    return candidate if os.path.isfile(candidate) else None
