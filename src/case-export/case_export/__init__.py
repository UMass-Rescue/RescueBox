"""
Job → JSON-LD fragment export (CASE/UCO-oriented, minimal dependencies).

Builds JSON-LD via ``case_uco.CASEGraph`` (CASE 1.4 / UCO 1.4 SDK). Use
``validate_fragment_jsonld`` for SHACL when ``case_validate`` is available
(``poetry install --with case-validation``).
"""

from case_export.fragment import build_case_fragment_from_job_dict
from case_export.hooks import on_job_completed
from case_export.persist import (
    build_jsonld_bytes_from_job_dict,
    case_exports_dir,
    write_case_fragment_file,
)
from case_export.validation import validate_fragment_jsonld

__all__ = [
    "build_case_fragment_from_job_dict",
    "build_jsonld_bytes_from_job_dict",
    "case_exports_dir",
    "on_job_completed",
    "validate_fragment_jsonld",
    "write_case_fragment_file",
]
