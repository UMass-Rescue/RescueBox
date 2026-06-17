import sqlite3
from pathlib import Path

import pytest

import frontend.database.job_db as job_db_module
from frontend.database.job_db import JobDB


def _job_columns(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("PRAGMA table_info(jobs)").fetchall()
    return {r[1] for r in rows}


@pytest.mark.asyncio
async def test_connect_bootstrap_contains_pipeline_columns(tmp_path: Path):
    db = JobDB(tmp_path / "jobs.db")
    conn = db.connect()
    cols = _job_columns(conn)
    assert "pipelineRootJobId" in cols
    assert "pipelineMetadataFilterCriteria" in cols


@pytest.mark.asyncio
async def test_initialize_schema_contains_pipeline_columns(tmp_path: Path):
    db = JobDB(tmp_path / "jobs.db")
    await db.initialize_schema()
    cols = _job_columns(db.connect())
    assert "pipelineRootJobId" in cols
    assert "pipelineMetadataFilterCriteria" in cols


def test_get_job_db_calls_shared_sync_initializer_once(monkeypatch):
    init_calls = {"count": 0}

    class FakeJobDB:
        def __init__(self):
            pass

        def _initialize_schema_sync(self):
            init_calls["count"] += 1

    monkeypatch.setattr(job_db_module, "JobDB", FakeJobDB)
    job_db_module._JOB_DB_SINGLETON["instance"] = None

    try:
        first = job_db_module.get_job_db()
        second = job_db_module.get_job_db()

        assert first is second
        assert init_calls["count"] == 1
    finally:
        job_db_module._JOB_DB_SINGLETON["instance"] = None
