"""Convert SQLite job rows to dicts ready for ``JobRecord`` validation."""

from __future__ import annotations

import json
import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


def row_to_job_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Parse JSON columns on a ``jobs`` row into a dict for ``JobRecord(**...)``."""
    job = dict(row)

    if job.get("request"):
        try:
            job["request"] = json.loads(job["request"])
        except json.JSONDecodeError as e:
            logger.error("Failed to parse request JSON: %s", e)
            job["request"] = {}

    if job.get("response"):
        try:
            job["response"] = json.loads(job["response"])
        except json.JSONDecodeError as e:
            logger.error("Failed to parse response JSON: %s", e)
            job["response"] = None

    if job.get("taskSchema"):
        try:
            job["taskSchema"] = json.loads(job["taskSchema"])
        except json.JSONDecodeError as e:
            logger.error("Failed to parse taskSchema JSON: %s", e)
            job["taskSchema"] = {}

    return job
