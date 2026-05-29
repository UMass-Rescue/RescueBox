"""
Context for pipeline job index (per-root-job SQLite) during result rendering.

Used so text/search renderers can enrich rows with source-image paths without
threading parameters through every ResultsPreview call site.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator, Optional, Tuple

_pipeline_root_job_id: ContextVar[Optional[str]] = ContextVar(
    "pipeline_root_job_id", default=None
)
_pipeline_user_id: ContextVar[Optional[str]] = ContextVar(
    "pipeline_user_id", default=None
)


def get_pipeline_index_ids() -> Tuple[Optional[str], Optional[str]]:
    """Return (user_id, root_job_id) for the active pipeline index, if any."""
    return _pipeline_user_id.get(), _pipeline_root_job_id.get()


@contextmanager
def pipeline_index_scope(
    pipeline_root_job_id: Optional[str],
    pipeline_user_id: Optional[str],
) -> Iterator[None]:
    """Set pipeline index context for nested result rendering."""
    t_root: Token = _pipeline_root_job_id.set(pipeline_root_job_id)
    t_user: Token = _pipeline_user_id.set(pipeline_user_id)
    try:
        yield
    finally:
        _pipeline_root_job_id.reset(t_root)
        _pipeline_user_id.reset(t_user)
