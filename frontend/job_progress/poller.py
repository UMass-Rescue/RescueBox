"""
Poll ``{job_id}.db`` every 10 seconds and mirror percent into ``jobs.statusText``.
"""

from __future__ import annotations

import asyncio
import logging

from frontend.job_progress.sync import mirror_progress_to_jobs_db

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 10.0


class JobProgressPoller:
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
