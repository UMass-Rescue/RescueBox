"""Read NiceGUI user storage values used by chatbot UI."""

from __future__ import annotations

from typing import Any

from frontend.utils.storage import read_user_storage_key


def read_pipeline_job_id() -> Any | None:
    """Return ``pipeline_job_id`` from user storage, or None if unavailable."""
    return read_user_storage_key("pipeline_job_id")
