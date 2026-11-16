from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from frontend.pages.chatbot.result_processor import ResultProcessor


@pytest.mark.asyncio
async def test_result_processor_reuses_injected_form_submit_handler():
    shared_handler = MagicMock()
    shared_handler.submit_form = AsyncMock(return_value=True)
    processor = ResultProcessor(
        state_manager=MagicMock(),
        tool_registry=MagicMock(),
        form_submit_handler=shared_handler,
    )

    ui_delegate = MagicMock(spec=["add_message", "show_error", "update_status", "set_input_enabled"])
    with patch(
        "frontend.pages.chatbot.result_processor.load_and_show_form",
        new_callable=AsyncMock,
    ) as mock_load_form:
        await processor.process_result(
            result={
                "type": "show_form",
                "endpoint": "audio/transcribe",
                "arguments": {},
            },
            container=MagicMock(),
            core=MagicMock(),
            ui_delegate=ui_delegate,
        )

    assert mock_load_form.await_count == 1
    assert mock_load_form.await_args.args[4] is shared_handler


@pytest.mark.asyncio
async def test_result_processor_falls_back_to_new_handler_when_not_injected():
    state_manager = MagicMock()
    processor = ResultProcessor(state_manager=state_manager, tool_registry=MagicMock())
    fake_handler = MagicMock()
    fake_handler.submit_form = AsyncMock(return_value=True)

    ui_delegate = MagicMock(spec=["add_message", "show_error", "update_status", "set_input_enabled"])
    with patch(
        "frontend.pages.chatbot.result_processor.FormSubmitHandler",
        return_value=fake_handler,
    ) as mock_handler_cls, patch(
        "frontend.pages.chatbot.result_processor.load_and_show_form",
        new_callable=AsyncMock,
    ) as mock_load_form:
        await processor.process_result(
            result={
                "type": "show_form",
                "endpoint": "audio/transcribe",
                "arguments": {},
            },
            container=MagicMock(),
            core=MagicMock(),
            ui_delegate=ui_delegate,
        )

    mock_handler_cls.assert_called_once_with(state_manager)
    assert mock_load_form.await_count == 1
    assert mock_load_form.await_args.args[4] is fake_handler


@pytest.mark.asyncio
async def test_process_result_show_form_uses_shared_handler_in_fallback_path():
    shared_handler = MagicMock()
    shared_handler.submit_form = AsyncMock(return_value=True)
    processor = ResultProcessor(
        state_manager=MagicMock(),
        tool_registry=MagicMock(),
        form_submit_handler=shared_handler,
    )

    ui_delegate = MagicMock(spec=["add_message", "show_error", "update_status", "set_input_enabled"])

    with patch(
        "frontend.pages.chatbot.result_processor.load_and_show_form",
        new_callable=AsyncMock,
    ) as mock_load_form:
        await processor.process_result(
            result={
                "type": "show_form",
                "endpoint": "audio/transcribe",
                "arguments": {},
            },
            container=MagicMock(),
            core=MagicMock(),
            ui_delegate=ui_delegate,
        )

    assert mock_load_form.await_count == 1
    assert mock_load_form.await_args.args[4] is shared_handler
