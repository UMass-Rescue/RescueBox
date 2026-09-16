"""Mirror ``{job_id}.db`` percent into ``jobs.db`` ``statusText``."""

from __future__ import annotations

from typing import Any

from rb.lib.job_progress import read_percent

from frontend.database import get_job_db


def running_progress_label(job_id: str) -> str | None:
    percent = read_percent(job_id)
    if percent is None:
        return None
    if percent <= 0:
        return "Running"
    return f"{percent}% done"


async def mirror_progress_to_jobs_db(job_id: str) -> str | None:
    text = running_progress_label(job_id)
    if text is None:
        return None
    await get_job_db().update_job_status_text(job_id, text)
    return text


async def mirror_running_jobs(jobs: list[dict[str, Any]]) -> None:
    for job in jobs:
        if job.get("status") != "Running":
            continue
        uid = job.get("uid")
        if not uid:
            continue
        text = await mirror_progress_to_jobs_db(uid)
        if text is not None:
            job["statusText"] = text
