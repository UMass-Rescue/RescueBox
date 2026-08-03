"""
Per-job SQLite progress files for long-running plugins.

Each active job has ``{RESCUEBOX_PROGRESS_DIR}/{job_id}.db`` with a single
``percent`` row. Frontend polls; backend updates from files processed / total.
Uses WAL and busy_timeout for concurrent access on Windows.
"""

from __future__ import annotations

import logging
import os
import platform
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from rb.lib.job_progress_context import get_current_job_id

logger = logging.getLogger(__name__)

_BUSY_TIMEOUT_MS = 15_000
_TABLE = "progress"


def progress_dir() -> Path:
    """Directory holding one ``{job_id}.db`` per running job."""
    env = os.getenv("RESCUEBOX_PROGRESS_DIR")
    if env:
        path = Path(env).expanduser()
    elif platform.system() == "Windows":
        base = Path(os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        path = base / "RescueBox" / "data" / "progress"
    else:
        path = Path.home() / ".rescuebox" / "data" / "progress"
    path.mkdir(parents=True, exist_ok=True)
    return path


def progress_db_path(job_id: str) -> Path:
    safe = job_id.replace("/", "_").replace("\\", "_")
    return progress_dir() / f"{safe}.db"


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=_BUSY_TIMEOUT_MS / 1000.0)
    conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {_TABLE} "
        "(id INTEGER PRIMARY KEY CHECK (id = 1), percent INTEGER NOT NULL, "
        "updated_at TEXT)"
    )
    conn.execute(f"INSERT OR IGNORE INTO {_TABLE} (id, percent) VALUES (1, 0)")
    conn.commit()
    conn.execute("PRAGMA journal_mode=WAL")


def init_job_progress_db(job_id: str) -> Path:
    """Create ``{job_id}.db`` with ``percent = 0``."""
    path = progress_db_path(job_id)
    conn = _connect(path)
    try:
        _ensure_schema(conn)
        conn.execute(f"UPDATE {_TABLE} SET percent = 0 WHERE id = 1")
        conn.commit()
    finally:
        conn.close()
    return path


def read_percent(job_id: str) -> int | None:
    path = progress_db_path(job_id)
    if not path.is_file():
        return None
    conn = _connect(path)
    try:
        row = conn.execute(f"SELECT percent FROM {_TABLE} WHERE id = 1").fetchone()
        return int(row[0]) if row else None
    except sqlite3.Error as exc:
        logger.debug("read_percent(%s): %s", job_id, exc)
        return None
    finally:
        conn.close()


def write_percent(job_id: str, percent: int) -> None:
    path = progress_db_path(job_id)
    conn = _connect(path)
    try:
        _ensure_schema(conn)
        stamp = datetime.now(timezone.utc).isoformat()
        conn.execute(
            f"UPDATE {_TABLE} SET percent = ?, updated_at = ? WHERE id = 1",
            (min(100, max(0, percent)), stamp),
        )
        conn.commit()
        logger.info("write job progress (%s):  %s percent", job_id, percent)
    finally:
        conn.close()


def delete_job_progress_db(job_id: str) -> None:
    path = progress_db_path(job_id)
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(path) + suffix) if suffix else path
        if candidate.is_file():
            try:
                candidate.unlink()
            except OSError as exc:
                logger.debug("delete %s: %s", candidate, exc)


def report_file_progress(
    job_id: str | None,
    processed: int,
    total: int,
    last_reported: int,
) -> int:
    """
    Update progress to ``processed / total`` (integer percent).

    Returns the new ``last_reported`` percent (unchanged if nothing written).
    """
    if not job_id:
        job_id = get_current_job_id()
    if not job_id or total <= 0:
        return last_reported
    pct = min(100, (processed * 100) // total)
    if pct > last_reported:
        pct = min(pct, 95)
        write_percent(job_id, pct)
        return pct
    return last_reported
