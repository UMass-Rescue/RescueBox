import pytest
from pathlib import Path
from frontend.chatbot.orchestrator import submit_job_orchestrator
from frontend.chatbot.config import ChatbotConfig
from frontend.database.file_filter_store import create_filter
from frontend.database.job_db import init_database
from fastapi import FastAPI, Body
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_orchestrator_posts_filter_meta_and_plugin_honors(tmp_path):
    await init_database()
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

    import sys

    repo_root = Path(__file__).resolve().parents[3]
    plugin_root = repo_root / "src" / "image-summary"
    if str(plugin_root) not in sys.path:
        sys.path.insert(0, str(plugin_root))
    from image_summary.main import summarize_images

    # Create a FastAPI app that exposes the plugin endpoint to emulate real HTTP integration.
    app = FastAPI()
    received_meta: dict = {}

    @app.post("/image_summary/summarize-images")
    async def run_plugin(payload: dict = Body(...)):
        inputs = payload.get("inputs", {})
        parameters = payload.get("parameters", {})
        received_meta.clear()
        received_meta.update(parameters.get("_meta") or {})
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

    response = await submit_job_orchestrator(None, http_client, config, request_dict, "/image_summary/summarize-images")
    rd = response.model_dump() if hasattr(response, "model_dump") else response
    assert rd is not None
    assert "root" in rd or (
        isinstance(rd, dict) and rd.get("output_type") is not None
    )
    assert received_meta.get("filterId") == fid
