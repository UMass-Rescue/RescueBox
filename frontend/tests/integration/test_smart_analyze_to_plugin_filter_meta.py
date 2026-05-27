import pytest
from pathlib import Path

from frontend.database.file_filter_store import create_filter
from frontend.pages.chatbot import DatabaseService
from frontend.database.job_db import init_database, get_job_db
from rb.api.models import RequestBody


@pytest.mark.asyncio
async def test_filter_meta_flow(tmp_path):
    # init DB
    db_path = tmp_path / "jobs.db"
    job_db = await init_database(db_path)

    # create a saved filter
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    f = input_dir / "i.jpg"
    f.write_text("x")
    fid = create_filter(name="t", input_dir=str(input_dir), paths=[str(f)], filter_type="input", owner_id="u1")

    # Simulate a request body coming from form submission with _meta.filterId
    request_body = RequestBody(
        inputs={},
        parameters={"_meta": {"filterId": fid}}
    )

    # Call create_and_track_job which should create job with filterId stored
    res = await DatabaseService.create_and_track_job(request_body, endpoint="image_summary/summarize-images", task_schema={})
    assert res is not None
    job_id = res.get("job_id")
    assert job_id

    # retrieve job and verify filterId persisted
    jd = await job_db.get_job_by_uid(job_id)
    assert jd is not None
    assert getattr(jd, "filterId", None) == fid
