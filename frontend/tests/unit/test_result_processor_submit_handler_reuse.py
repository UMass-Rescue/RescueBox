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

    submit_cb = processor._create_form_submit_handler(
        container=MagicMock(), core=MagicMock()
    )
    request_body = {"inputs": {}}
    task_schema = {"k": "v"}
    await submit_cb(request_body, endpoint="audio/transcribe", task_schema=task_schema)

    shared_handler.submit_form.assert_awaited_once()


@pytest.mark.asyncio
async def test_result_processor_falls_back_to_new_handler_when_not_injected():
    processor = ResultProcessor(state_manager=MagicMock(), tool_registry=MagicMock())
    fake_handler = MagicMock()
    fake_handler.submit_form = AsyncMock(return_value=True)

    with patch(
        "frontend.pages.chatbot.result_processor.FormSubmitHandler",
        return_value=fake_handler,
    ) as mock_handler_cls:
        submit_cb = processor._create_form_submit_handler(
            container=MagicMock(),
            core=MagicMock(),
        )
        await submit_cb({"inputs": {}}, endpoint="audio/transcribe", task_schema={})

    mock_handler_cls.assert_called_once()
    fake_handler.submit_form.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_result_show_form_uses_shared_handler_in_fallback_path():
    shared_handler = MagicMock()
    shared_handler.submit_form = AsyncMock(return_value=True)
    processor = ResultProcessor(
        state_manager=MagicMock(),
        tool_registry=MagicMock(),
        form_submit_handler=shared_handler,
    )

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
            add_message_callback=MagicMock(),
            show_error_callback=MagicMock(),
            update_status_callback=MagicMock(),
            load_form_callback=None,
            set_input_enabled_callback=MagicMock(),
        )

    assert mock_load_form.await_count == 1
    submit_cb = mock_load_form.await_args.args[4]
    await submit_cb({"inputs": {}}, endpoint="audio/transcribe", task_schema={})
    shared_handler.submit_form.assert_awaited_once()
