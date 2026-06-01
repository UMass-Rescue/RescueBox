import pytest
from frontend.chatbot.orchestrator import submit_job_orchestrator
from frontend.chatbot.config import ChatbotConfig
from frontend.database.file_filter_store import create_filter
from frontend.database.job_db import init_database
from fastapi import FastAPI, Body
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_orchestrator_posts_filter_meta_and_plugin_honors(tmp_path):
    db_path = tmp_path / "jobs.db"
    await init_database(db_path)
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    img = input_dir / "imgA.jpg"
    img.write_text("dummy")

    fid = create_filter(
        name="filt",
        input_dir=str(input_dir),
        paths=[str(img.name)],
        filter_type="composite",
        owner_id="u1",
    )
    assert fid

    # Prepare request payload that would be posted by orchestrator
    request_dict = {
        "inputs": {
            "input_dir": {"path": str(input_dir)},
            "output_dir": {"path": str(tmp_path / "out")},
        },
        "parameters": {"model": "gemma3:4b", "_meta": {"filterId": fid}},
    }

    # Create a FastAPI app that exposes the plugin endpoint to emulate real HTTP integration.
    app = FastAPI()
    received_meta: dict = {}

    @app.post("/image_summary/summarize-images")
    async def run_plugin(payload: dict = Body(...)):
        payload.get("inputs", {})
        parameters = payload.get("parameters", {})
        received_meta.clear()
        received_meta.update(parameters.get("_meta") or {})
        return {
            "root": {
                "output_type": "text",
                "value": "mocked summary",
                "title": "Mocked Result",
            }
        }

    http_client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    config = ChatbotConfig(RESCUEBOX_HOST="http://test")

    response = await submit_job_orchestrator(
        None, http_client, config, request_dict, "/image_summary/summarize-images"
    )
    rd = response.model_dump() if hasattr(response, "model_dump") else response
    assert rd is not None
    assert "root" in rd or (isinstance(rd, dict) and rd.get("output_type") is not None)
    assert received_meta.get("filterId") == fid
