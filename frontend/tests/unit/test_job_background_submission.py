import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from frontend.pages.chatbot.utils.job_submission_orchestrator import JobSubmissionOrchestrator
from frontend.pages.chatbot.utils import job_submission_orchestrator as orchestrator_module


@pytest.mark.asyncio
async def test_background_submission_schedules_background_task(monkeypatch):
    form_handler = MagicMock()
    form_handler.state_manager = MagicMock()
    orchestrator = JobSubmissionOrchestrator(form_handler)

    # Patch conversation manager to return a conversation id
    orchestrator.conversation_manager.ensure_conversation = AsyncMock(return_value="conv1")

    # Patch DatabaseService.create_and_track_job to return a job id
    monkeypatch.setattr(orchestrator_module, "DatabaseService", MagicMock())
    orchestrator_module.DatabaseService.create_and_track_job = AsyncMock(return_value={"job_id": "JOB_TEST"})

    # Patch background_tasks.create to capture scheduling
    called = {"count": 0}

    def fake_create(coro, name=None, handle_exceptions=False):
        called["count"] += 1
        # do not run coroutine
    monkeypatch.setattr(orchestrator_module.background_tasks, "create", fake_create)

    # Prepare dummy request body and core
    request_body = MagicMock()
    request_body.inputs = {}
    request_body.parameters = {}
    core = MagicMock()
    core.api = None
    core.api_client = None
    core.config = MagicMock()
    core.config.RESCUEBOX_HOST = "http://localhost:8000"

    res = await orchestrator._execute_job(request_body, "audio/transcribe", {}, None, core)
    # _execute_job returns immediately; background task scheduled
    assert called["count"] == 1
