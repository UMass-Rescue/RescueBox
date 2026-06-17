"""Unit tests for FormSubmitHandler (active case gate and orchestration wiring)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from frontend.pages.chatbot.form_submit_handler import FormSubmitHandler
from frontend.pages.chatbot.state import ChatbotStateManager


@pytest.mark.asyncio
async def test_submit_form_returns_false_without_active_case():
    handler = FormSubmitHandler(ChatbotStateManager())
    core = MagicMock()
    with patch(
        "frontend.pages.chatbot.form_submit_handler.ensure_active_case_id",
        return_value=None,
    ):
        ok = await handler.submit_form(
            request_body=MagicMock(),
            endpoint="audio/transcribe",
            task_schema=MagicMock(),
            container=MagicMock(),
            core=core,
        )
    assert ok is False
    core.submit_job.assert_not_called()


@pytest.mark.asyncio
async def test_submit_form_aborts_when_case_notes_cancelled():
    handler = FormSubmitHandler(ChatbotStateManager())
    with patch(
        "frontend.pages.chatbot.form_submit_handler.ensure_active_case_id",
        return_value="demo_abc",
    ), patch(
        "frontend.pages.chatbot.form_submit_handler.show_case_notes_dialog",
        new_callable=AsyncMock,
        return_value=None,
    ), patch.object(
        handler.job_orchestrator, "submit_job", new_callable=AsyncMock
    ) as mock_submit:
        ok = await handler.submit_form(
            request_body=MagicMock(),
            endpoint="audio/transcribe",
            task_schema=MagicMock(),
            container=MagicMock(),
            core=MagicMock(),
        )
    assert ok is False
    mock_submit.assert_not_awaited()
