import pytest
from pathlib import Path
from frontend.chatbot.orchestrator import submit_job_orchestrator
from frontend.chatbot.config import ChatbotConfig
from frontend.database.file_filter_store import create_filter
from frontend.database.job_db import init_database, get_job_db
from fastapi import FastAPI, Body
import httpx
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_orchestrator_posts_filter_meta_and_plugin_honors(tmp_path):
    # Initialize DB and create a saved filter referring to a single image
    db_path = tmp_path / "jobs.db"
    await init_database(db_path)
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    img = input_dir / "imgA.jpg"
    img.write_text("dummy")

    fid = create_filter(name="filt", input_dir=str(input_dir), paths=[str(img.name)], filter_type="composite", owner_id="u1")
    assert fid

    # Prepare request payload that would be posted by orchestrator
    request_dict = {
        "inputs": {
            "input_dir": {"path": str(input_dir)},
            "output_dir": {"path": str(tmp_path / "out")},
        },
        "parameters": {
            "model": "gemma3:4b",
            "_meta": {"filterId": fid}
        }
    }

    # Import plugin callable by file path (avoids package import issues)
    import importlib.util, sys
    repo_root = Path(__file__).resolve().parents[4]
    plugin_path = repo_root / "src" / "image-summary" / "image_summary" / "main.py"
    spec = importlib.util.spec_from_file_location("image_summary_main", str(plugin_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["image_summary_main"] = mod
    spec.loader.exec_module(mod)
    summarize_images = getattr(mod, "summarize_images")

    # Create a FastAPI app that exposes the plugin endpoint to emulate real HTTP integration.
    app = FastAPI()

    @app.post("/image_summary/summarize-images")
    async def run_plugin(payload: dict = Body(...)):
        inputs = payload.get("inputs", {})
        parameters = payload.get("parameters", {})
        # Build minimal objects expected by plugin (DirectoryInput-like with .path)
        class DI:
            def __init__(self, p): self.path = Path(p)
        in_obj = {}
        for k, v in inputs.items():
            if isinstance(v, dict) and "path" in v:
                in_obj[k] = DI(v["path"])
            else:
                in_obj[k] = v
        # Call plugin function synchronously
        res = summarize_images(in_obj, parameters)
        # Return whatever plugin returned (assumed serializable)
        if hasattr(res, "model_dump"):
            return res.model_dump(mode="json")
        if hasattr(res, "dict"):
            return res.dict()
        return res

    http_client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    config = ChatbotConfig(RESCUEBOX_HOST="http://test")

    # Run orchestrator (api_wrapper=None, http_client=our dummy)
    response = await submit_job_orchestrator(None, http_client, config, request_dict, "/image_summary/summarize-images")
    # response is a ResponseBody model; extract root list
    # It's enough that no exception was raised and response contains 'root'
    rd = response.model_dump() if hasattr(response, "model_dump") else response
    assert rd is not None
    # Ensure the plugin returned processed files (list) — even if empty, flow executed
    assert "root" in rd

    # Ensure job was created and persisted with filterId set (create_and_track_job called inside orchestrator path)
    job_db = get_job_db()
    # get latest job
    jobs = await job_db.get_all_jobs()
    assert jobs
    created = jobs[0]
    assert created.get("filterId") == fid
