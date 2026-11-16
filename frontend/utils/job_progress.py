"""
Job progress tracking and statusText synchronization.

Manages per-job progress SQLite files under RESCUEBOX_PROGRESS_DIR
and synchronizes execution percentage into jobs.db statusText.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from rb.lib.job_progress import (
    delete_job_progress_db,
    init_job_progress_db,
    read_percent,
)

from frontend.database import get_job_db

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 10.0


def init_job_progress(job_id: str) -> None:
    """Initialize a progress tracking file for the given job ID."""
    init_job_progress_db(job_id)


def cleanup_job_progress(job_id: str | None) -> None:
    """Delete the progress tracking file for the given job ID if present."""
    if job_id:
        delete_job_progress_db(job_id)


def running_progress_label(job_id: str) -> str | None:
    """Read progress percent and format as a status label."""
    percent = read_percent(job_id)
    if percent is None:
        return None
    if percent <= 0:
        return "Running"
    return f"{percent}% done"


async def mirror_progress_to_jobs_db(job_id: str) -> str | None:
    """Read current job progress and update statusText in jobs.db."""
    text = running_progress_label(job_id)
    if text is None:
        return None
    await get_job_db().update_job_status_text(job_id, text)
    return text


async def mirror_running_jobs(jobs: list[dict[str, Any]]) -> None:
    """Update statusText for any jobs with status 'Running'."""
    for job in jobs:
        if job.get("status") != "Running":
            continue
        uid = job.get("uid")
        if not uid:
            continue
        text = await mirror_progress_to_jobs_db(uid)
        if text is not None:
            job["statusText"] = text


class JobProgressPoller:
    """Polls {job_id}.db every 10 seconds and mirrors percent into jobs.statusText."""

    def __init__(self, job_id: str) -> None:
        self._job_id = job_id
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            await self._task

    async def _run(self) -> None:
        while not self._stop.is_set():
            await self._sync_once()
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=POLL_INTERVAL_SEC)
                break
            except TimeoutError:
                continue

    async def _sync_once(self) -> None:
        try:
            await mirror_progress_to_jobs_db(self._job_id)
        except Exception as exc:
            logger.debug("progress poll for %s: %s", self._job_id, exc)


__all__ = [
    "JobProgressPoller",
    "cleanup_job_progress",
    "init_job_progress",
    "mirror_progress_to_jobs_db",
    "mirror_running_jobs",
    "running_progress_label",
]
