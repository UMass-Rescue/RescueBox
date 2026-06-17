"""Write JSON-LD fragments next to RescueBox frontend data (optional cache on job complete)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from case_export.fragment import build_jsonld_text

logger = logging.getLogger(__name__)


def case_exports_dir() -> Path:
    """Directory for cached CASE fragments: ``frontend/data/case_exports``."""
    here = Path(__file__).resolve().parent
    rescuebox_root = here.parent.parent.parent
    d = rescuebox_root / "frontend" / "data" / "case_exports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def build_jsonld_bytes_from_job_dict(job: Dict[str, Any]) -> bytes:
    return build_jsonld_text(job).encode("utf-8")


def write_case_fragment_file(job_uid: str, job: Dict[str, Any]) -> Path:
    """Write ``{job_uid}.jsonld`` under case_exports_dir."""
    path = case_exports_dir() / f"{job_uid}.jsonld"
    path.write_text(build_jsonld_text(job), encoding="utf-8")
    logger.debug("Wrote CASE fragment: %s", path)
    return path
