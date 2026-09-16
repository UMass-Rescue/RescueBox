"""
Integration tests for post-refactor chatbot modules (no live backend required).

Covers pipeline planning, handler boundaries, and UI-flow helpers that moved out of
``pages.chatbot.handlers`` into ``ui_flow``, ``pipeline_planner``, and ``pipeline_context``.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from rb.api.models import (
    DirectoryResponse,
    FileResponse,
    FileType,
    InputType,
    ResponseBody,
)

from frontend.chatbot.pipeline_context import inject_pipeline_path
from frontend.database.job_db import init_database
from frontend.pages.chatbot import handlers, ui_flow
from frontend.pages.chatbot.handlers.pipeline import PipelineHandler
from frontend.pages.chatbot.handlers.pipeline_planner import plan_next_pipeline_step


@pytest.mark.integration
def test_handlers_package_surface_matches_refactor():
    """Job orchestration lives under handlers; form/results UI lives in ui_flow."""
    assert "JobSubmissionOrchestrator" in handlers.__all__
    assert "PipelineHandler" in handlers.__all__
    assert "load_and_show_form" not in handlers.__all__
    assert hasattr(ui_flow, "load_and_show_form")
    assert hasattr(ui_flow, "show_tool_picker")


@pytest.mark.integration
def test_pipeline_handler_has_remaining():
    orchestrator = SimpleNamespace()
    handler = PipelineHandler(orchestrator)
    assert handler.has_remaining([{"endpoint": "a/b"}]) is True
    assert handler.has_remaining([]) is False
    assert handler.has_remaining(None) is False


@pytest.mark.integration
def test_plan_next_pipeline_step_chains_directory_output():
    """Planner wires multi_tool chaining without NiceGUI or HTTP."""
    previous = ResponseBody(
        root=DirectoryResponse(
            output_type="directory",
            path="/output/chained",
            title="Out",
        )
    )
    next_schema = SimpleNamespace(
        inputs=[
            SimpleNamespace(
                key="input_dir",
                input_type=InputType.DIRECTORY,
            )
        ]
    )
    plan = plan_next_pipeline_step(
        previous,
        {"endpoint": "deepfake_detection/predict", "arguments": {"input_dir": "/tmp"}},
        next_schema,
    )
    assert plan.next_endpoint == "deepfake_detection/predict"
    assert plan.next_arguments.get("input_dir") == "/output/chained"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_inject_pipeline_path_uses_completed_job_in_sqlite(tmp_path):
    """``load_and_show_form`` path: pipeline_job_id resolves via real job DB."""
    db = await init_database(tmp_path / "jobs.db")
    out_path = tmp_path / "pipeline_out"
    out_path.mkdir()
    job = await db.create_job(
        request_body={"inputs": {}, "parameters": {}},
        task_schema={},
        endpoint="image_summary/summarize-images",
    )
    response = ResponseBody(
        FileResponse(
            filename="out.txt",
            content="done",
            file_type=FileType.TEXT,
            path=str(out_path / "out.txt"),
            title="out",
        )
    )
    await db.update_job_status(job.uid, "Completed", response_body=response)

    schema = SimpleNamespace(
        inputs=[
            SimpleNamespace(key="input_dir", input_type=InputType.DIRECTORY),
        ]
    )
    merged = inject_pipeline_path({"prompt": "x"}, schema, job.uid)
    assert merged["prompt"] == "x"
    assert Path(merged["input_dir"]).resolve() == out_path.resolve()
