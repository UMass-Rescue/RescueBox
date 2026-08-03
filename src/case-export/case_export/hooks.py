"""Hook when a job completes: cache JSON-LD fragment (best-effort)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def on_job_completed(job_uid: str) -> None:
    try:
        from case_export.persist import write_case_fragment_file
        from frontend.database import get_job_db
        from frontend.pages.jobs import extract_job_fields
    except Exception as e:
        logger.debug("CASE export hook imports failed: %s", e)
        return

    try:
        job_db = get_job_db()
        job = await job_db.get_job_by_uid(job_uid)
        if not job:
            return
        fields = extract_job_fields(job)
        if str(fields.get("status", "")).lower() not in ("completed",):
            return
        write_case_fragment_file(job_uid, fields)
    except Exception:
        logger.debug("CASE fragment cache failed for %s", job_uid, exc_info=True)
