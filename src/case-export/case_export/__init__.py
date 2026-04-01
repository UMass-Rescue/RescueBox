"""
Job → JSON-LD fragment export (CASE/UCO-oriented, minimal dependencies).

Optional: install ``case-uco`` later for stricter typing; the default path builds
JSON-LD with UCO/CASE namespace prefixes (fragment-only; not SHACL-validated).
"""

from case_export.fragment import build_case_fragment_from_job_dict
from case_export.hooks import on_job_completed
from case_export.persist import (
    build_jsonld_bytes_from_job_dict,
    case_exports_dir,
    write_case_fragment_file,
)

__all__ = [
    "build_case_fragment_from_job_dict",
    "case_exports_dir",
    "write_case_fragment_file",
    "build_jsonld_bytes_from_job_dict",
    "on_job_completed",
]
