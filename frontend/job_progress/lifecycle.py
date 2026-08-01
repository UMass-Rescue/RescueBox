"""Create and remove per-job progress SQLite files."""

from __future__ import annotations

from rb.lib.job_progress import delete_job_progress_db, init_job_progress_db


def init_job_progress(job_id: str) -> None:
    init_job_progress_db(job_id)


def cleanup_job_progress(job_id: str | None) -> None:
    if job_id:
        delete_job_progress_db(job_id)
