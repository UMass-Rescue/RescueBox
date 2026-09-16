from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from frontend.pages.chatbot.handlers import JobSubmissionOrchestrator
from frontend.pages.chatbot.handlers import job_orchestrator as orchestrator_module


@pytest.mark.asyncio
async def test_background_submission_schedules_background_task(monkeypatch):
    form_handler = MagicMock()
    form_handler.state_manager = MagicMock()
    orchestrator = JobSubmissionOrchestrator(form_handler)

    # Patch lifecycle service to return a tracked job id.
    orchestrator.lifecycle.create_tracked_job = AsyncMock(return_value="JOB_TEST")

    # Patch background_tasks.create to capture scheduling
    called = {"count": 0}

    def fake_create_capture_count(coroutine, name=None, handle_exceptions=False):
        called["count"] += 1
        coroutine.close()

    monkeypatch.setattr(
        orchestrator_module.background_tasks, "create", fake_create_capture_count
    )

    # Prepare dummy request body and core
    request_body = MagicMock()
    request_body.inputs = {}
    request_body.parameters = {}
    core = MagicMock()
    core.api = None
    core.api_client = None
    core.config = MagicMock()
    core.config.RESCUEBOX_HOST = "http://localhost:8000"

    await orchestrator._execute_job(request_body, "audio/transcribe", {}, None, core)
    # _execute_job returns immediately; background task scheduled
    assert called["count"] == 1


@pytest.mark.asyncio
async def test_background_submission_success_enables_input(monkeypatch):
    """Test that a successful job completion (with no remaining calls) re-enables the chat input."""
    form_handler = MagicMock()
    form_handler.state_manager = MagicMock()
    orchestrator = JobSubmissionOrchestrator(form_handler)

    with patch(
        "frontend.pages.chatbot.handlers.job_orchestrator.show_results",
        new_callable=AsyncMock,
    ), patch(
        "frontend.pages.chatbot.handlers.job_lifecycle_service.DatabaseService.save_tool_result_to_history",
        new_callable=AsyncMock,
    ), patch(
        "frontend.components.chat.ui_operations.UIOperations.safe_container_update",
        new_callable=AsyncMock,
    ), patch(
        "frontend.components.chat.ui_operations.UIOperations.scroll_to_bottom_after_dom_update",
        new_callable=AsyncMock,
    ):

        await orchestrator._handle_success(
            _request_body=None,
            endpoint="test",
            task_schema=None,
            container=MagicMock(),
            core=MagicMock(),
            remaining_calls=None,
            conversation_id="conv1",
            response_body=MagicMock(),
            job_info={"job_id": "job1"},
        )
        form_handler.state_manager.set_input_enabled.assert_called_with(True)


@pytest.mark.asyncio
async def test_tracked_single_job_skips_chat_results_after_redirect(monkeypatch):
    """After redirect to /jobs, background success must not touch the chat container."""
    form_handler = MagicMock()
    form_handler.state_manager = MagicMock()
    orchestrator = JobSubmissionOrchestrator(form_handler)
    orchestrator.lifecycle.record_job_started = AsyncMock()
    orchestrator.lifecycle.complete_successful_submission = AsyncMock()

    show_results_mock = AsyncMock()
    navigate_scheduled: list[int] = []

    monkeypatch.setattr(orchestrator_module, "show_results", show_results_mock)
    monkeypatch.setattr(
        orchestrator_module,
        "_schedule_jobs_page_navigation",
        lambda: navigate_scheduled.append(1),
    )

    core = MagicMock()
    core.submit_job = AsyncMock(return_value=MagicMock())

    await orchestrator._run_successful_submit(
        request_body=MagicMock(),
        endpoint="test/endpoint",
        task_schema=MagicMock(),
        target_container=MagicMock(),
        core=core,
        remaining_calls=None,
        conversation_id="conv1",
        job_id="JOB_abc",
        loading_row=None,
    )

    show_results_mock.assert_not_called()


@pytest.mark.asyncio
async def test_handle_remaining_calls_passes_on_form_cancel():
    """Test that handle_remaining_calls properly passes on_form_cancel to load_and_show_form."""
    form_handler = MagicMock()
    form_handler.state_manager = MagicMock()
    orchestrator = JobSubmissionOrchestrator(form_handler)

    remaining_calls = [{"endpoint": "test/endpoint", "arguments": {}}]
    response_body = MagicMock()
    container = MagicMock()
    container.__enter__ = MagicMock(return_value=container)
    container.__exit__ = MagicMock(return_value=None)
    core = MagicMock()
    core.get_task_schema_from_endpoint = AsyncMock(return_value=MagicMock())

    with patch(
        "frontend.pages.chatbot.handlers.pipeline.load_and_show_form",
        new_callable=AsyncMock,
    ) as mock_load, patch(
        "frontend.pages.chatbot.handlers.pipeline.coerce_pipeline_response",
        return_value=response_body,
    ), patch(
        "frontend.pages.chatbot.handlers.pipeline.extract_batch_file_items",
        return_value=[],
    ), patch(
        "frontend.pages.chatbot.handlers.pipeline.chain_output_to_input",
        return_value={},
    ):

        await orchestrator.handle_remaining_calls(
            remaining_calls, response_body, container, core
        )

        mock_load.assert_called_once()
        kwargs = mock_load.call_args.kwargs
        assert "on_form_cancel" in kwargs

        # Test the cancel callback re-enables the input
        cancel_cb = kwargs["on_form_cancel"]
        cancel_cb()
        form_handler.state_manager.set_input_enabled.assert_called_with(True)


@pytest.mark.asyncio
async def test_do_submit_error_enables_input(monkeypatch):
    """Test that a job failure in the background task gracefully catches the error and re-enables the chat input."""
    form_handler = MagicMock()
    form_handler.state_manager = MagicMock()
    orchestrator = JobSubmissionOrchestrator(form_handler)

    do_submit_coro = None

    def fake_create_store_coro(coroutine, name=None, handle_exceptions=False):
        nonlocal do_submit_coro
        do_submit_coro = coroutine

    monkeypatch.setattr(
        orchestrator_module.background_tasks, "create", fake_create_store_coro
    )

    core = MagicMock()
    core.config = MagicMock()
    core.config.RESCUEBOX_HOST = "http://localhost"
    core.submit_job = AsyncMock(side_effect=RuntimeError("Simulated API failure"))

    with patch(
        "frontend.pages.chatbot.handlers.job_lifecycle_service.DatabaseService.create_and_track_job",
        new_callable=AsyncMock,
        return_value={"job_id": "job1"},
    ), patch(
        "frontend.pages.chatbot.handlers.job_lifecycle_service.DatabaseService.save_user_prompt_if_missing_from_form_submission",
        new_callable=AsyncMock,
    ), patch(
        "frontend.pages.chatbot.handlers.job_lifecycle_service.DatabaseService.update_job_status",
        new_callable=AsyncMock,
    ):

        request_body = MagicMock()
        request_body.inputs = {}
        request_body.parameters = {}

        await orchestrator._execute_job(
            request_body, "test/endpoint", MagicMock(), MagicMock(), core
        )

        assert do_submit_coro is not None
        # Run the captured background task to trigger the exception block internally
        await do_submit_coro

        # Verify state manager was commanded to stop processing and re-enable input
        form_handler.state_manager.set_processing.assert_called_with(False)
        form_handler.state_manager.set_input_enabled.assert_called_with(True)
