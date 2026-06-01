from pathlib import Path
import pytest

from frontend.database.job_db import init_database
from frontend.database.file_filter_store import (
    create_filter,
    load_filter,
    resolve_filter_for_job,
)
from frontend.database.file_filter_utils import (
    process_prompt_for_filters,
    set_job_filter,
)


@pytest.mark.asyncio
async def test_create_and_load_filter(tmp_path):
    db_path = tmp_path / "jobs.db"
    # initialize DB
    await init_database(db_path)
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    f = input_dir / "img1.jpg"
    f.write_text("dummy")

    fid = create_filter(name="f1", input_dir=str(input_dir), paths=[str(f)], filter_type="input", owner_id="u1")
    assert fid is not None
    loaded = load_filter(fid)
    assert loaded is not None
    assert fid == loaded["id"]
    assert str(f) in loaded.get("paths_json", [])


@pytest.mark.asyncio
async def test_resolve_and_persist_input_filter(tmp_path):
    db_path = tmp_path / "jobs.db"
    await init_database(db_path)
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    f = input_dir / "img2.jpg"
    f.write_text("dummy")

    # pass list of files (strings) and request persistence
    paths, fid = resolve_filter_for_job([str(f)], input_dir, persist_if_requested=True, owner_id="u1")
    assert paths and isinstance(paths[0], Path)
    assert fid is not None
    loaded = load_filter(fid)
    assert loaded and "img2.jpg" in loaded.get("paths_json", [])


@pytest.mark.asyncio
async def test_resolve_and_persist_output_filter_and_composite(tmp_path):
    db_path = tmp_path / "jobs.db"
    await init_database(db_path)
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    f = input_dir / "img3.jpg"
    f.write_text("dummy")

    out_file = tmp_path / "patterns.txt"
    out_file.write_text("cat\n>=0.5\n")

    # call process_prompt_for_filters with persist requested
    tool_call = {"arguments": {"file_filter": [str(f)], "output_filter": [str(out_file)]}}
    fid = process_prompt_for_filters("find cat", tool_call, input_dir=input_dir, owner_id="u1", persist_if_requested=True)
    assert fid is not None
    loaded = load_filter(fid)
    assert loaded is not None
    assert loaded.get("paths_json") is not None or loaded.get("patterns_json") is not None


@pytest.mark.asyncio
async def test_set_job_filter_attaches_to_job(tmp_path):
    db_path = tmp_path / "jobs.db"
    job_db = await init_database(db_path)

    # create a minimal job
    request_body = {"inputs": {}, "parameters": {}}
    task_schema = {}
    job_record = await job_db.create_job(request_body=request_body, task_schema=task_schema, endpoint="test/ep")
    assert job_record is not None

    fid = create_filter(name="f2", input_dir=str(tmp_path), paths=[], filter_type="input", owner_id="u1")
    assert fid is not None

    # set filter on job
    ok = set_job_filter(job_db, job_record.uid, filter_id=fid)
    assert ok

    job2 = await job_db.get_job_by_uid(job_record.uid)
    assert job2 is not None
    assert getattr(job2, "filterId", None) == fid

