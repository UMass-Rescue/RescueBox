"""Durable queue of uploads awaiting delivery, and the worker that delivers them."""

import asyncio
import logging
import os
import sqlite3
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .remote import RemoteError

logger = logging.getLogger(__name__)
IDLE_SECONDS = 60.0
MAX_BACKOFF = 300.0

SCHEMA = """
PRAGMA secure_delete = ON;
PRAGMA user_version = 1;
CREATE TABLE IF NOT EXISTS outbox (
  sha256 TEXT NOT NULL,
  investigator_email TEXT NOT NULL,
  essay_version INTEGER NOT NULL,
  essay TEXT,
  file_name TEXT,
  state TEXT NOT NULL CHECK (state IN ('pending', 'failed')),
  error TEXT,
  generation INTEGER NOT NULL DEFAULT 0,
  queued_at REAL NOT NULL,
  PRIMARY KEY (sha256, investigator_email));
CREATE INDEX IF NOT EXISTS outbox_queue ON outbox (state, queued_at);
"""

# Coalesce so the API ends in the state that delivering every upload in order gives:
# only a strictly newer version replaces an essay, and a file name is never dropped.
PUT = """
INSERT INTO outbox
  (sha256, investigator_email, essay_version, essay, file_name, state, queued_at)
VALUES (?, ?, ?, ?, ?, 'pending', ?)
ON CONFLICT (sha256, investigator_email) DO UPDATE SET
  essay = CASE WHEN state = 'failed' OR excluded.essay_version > essay_version
               THEN excluded.essay ELSE essay END,
  essay_version = CASE WHEN state = 'failed' OR excluded.essay_version > essay_version
                       THEN excluded.essay_version ELSE essay_version END,
  file_name = coalesce(excluded.file_name, file_name),
  state = 'pending', error = NULL, generation = generation + 1,
  queued_at = excluded.queued_at
"""

NEXT = """
SELECT sha256, investigator_email, essay_version, essay, file_name, generation
FROM outbox WHERE state = 'pending' ORDER BY queued_at LIMIT 1
"""

# Worker writes apply only to the generation they read, so an upload that arrives
# during delivery is never deleted or failed by the older delivery's outcome.
GUARD = " WHERE sha256 = ? AND investigator_email = ? AND generation = ?"


@dataclass(frozen=True)
class Pending:
    item: dict
    generation: int


class Outbox:
    """SQLite queue with one row per file and investigator; None keeps it in memory."""

    def __init__(self, path: Path | None, clock: Callable[[], float] = time.time):
        self.db = sqlite3.connect(_private(path) if path else ":memory:")
        self.db.isolation_level = None
        self.db.executescript(SCHEMA)
        self.clock = clock

    def put(self, item: dict) -> None:
        values = (item["sha256"], item["investigator_email"], item["essay_version"])
        extra = (item["essay"], item.get("file_name"), self.clock())
        self.db.execute(PUT, values + extra)

    def next_due(self) -> Pending | None:
        row = self.db.execute(NEXT).fetchone()
        if row is None:
            return None
        sha256, email, version, essay, file_name, generation = row
        item = {"sha256": sha256, "investigator_email": email, "essay_version": version}
        item["essay"] = essay
        if file_name is not None:
            item["file_name"] = file_name
        return Pending(item, generation)

    def delivered(self, row: Pending) -> None:
        self._guarded("DELETE FROM outbox", row)

    def rejected(self, row: Pending, error: str) -> None:
        sql = "UPDATE outbox SET state = 'failed', essay = NULL, error = ?"
        self._guarded(sql, row, error)

    def deferred(self, row: Pending) -> None:
        self._guarded("UPDATE outbox SET queued_at = ?", row, self.clock())

    def counts(self) -> dict[str, int]:
        rows = self.db.execute("SELECT state, count(*) FROM outbox GROUP BY state")
        return {"pending": 0, "failed": 0, **dict(rows.fetchall())}

    def close(self) -> None:
        self.db.close()

    def _guarded(self, statement: str, row: Pending, *values: object) -> None:
        key = (row.item["sha256"], row.item["investigator_email"], row.generation)
        self.db.execute(statement + GUARD, values + key)


def _private(path: Path) -> str:
    """Create the directory and database readable by their owner only."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.close(os.open(path, os.O_CREAT | os.O_WRONLY, 0o600))
    return str(path)


class Uploader(Protocol):
    async def upload(self, item: dict) -> None: ...


class Worker:
    """Deliver queued uploads one at a time; pause all delivery while the API fails."""

    def __init__(
        self,
        outbox: Outbox,
        remote: Uploader,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        idle: float = IDLE_SECONDS,
    ):
        self.outbox, self.remote, self.sleep, self.idle = outbox, remote, sleep, idle
        self.wake = asyncio.Event()
        self.backoff = 0.0

    async def run(self) -> None:
        while True:
            try:
                await self.step()
            except Exception as error:
                logger.error("outbox_worker_failed %s", type(error).__name__)
                await self._pause(None)

    async def step(self) -> None:
        self.wake.clear()
        row = self.outbox.next_due()
        if row is None:
            await self._wait()
            return
        try:
            await self.remote.upload(row.item)
        except RemoteError as error:
            await self._failed(row, error)
            return
        self.outbox.delivered(row)
        self.backoff = 0.0

    async def _wait(self) -> None:
        try:
            await asyncio.wait_for(self.wake.wait(), self.idle)
        except TimeoutError:
            pass

    async def _failed(self, row: Pending, error: RemoteError) -> None:
        if error.kind == "rejected":
            logger.warning("upload_rejected %s %s", error.code, error.request_id)
            self.outbox.rejected(row, ":".join([error.code, *error.fields]))
            self.backoff = 0.0
            return
        logger.warning("upload_deferred %s %s", error.kind, error.status)
        self.outbox.deferred(row)
        await self._pause(error.retry_after)

    async def _pause(self, retry_after: float | None) -> None:
        self.backoff = min(
            MAX_BACKOFF, max(retry_after or 0.0, 2 * self.backoff or 1.0)
        )
        await self.sleep(self.backoff)
