from unittest.mock import AsyncMock, MagicMock

import pytest

from frontend.pages.chatbot import ChatUIDelegate, MessageFlowCoordinator

# pylint: disable=protected-access


def test_coordinator_uses_single_shared_form_submit_handler():
    state_manager = MagicMock()
    coordinator = MessageFlowCoordinator(state_manager)

    assert coordinator.form_submit_handler is not None
    assert (
        coordinator.result_processor.form_submit_handler
        is coordinator.form_submit_handler
    )


def test_coordinator_direct_dependency_injection():
    state_manager = MagicMock()
    message_handler = MagicMock()
    tool_registry = MagicMock()
    ui_delegate = MagicMock()

    coordinator = MessageFlowCoordinator(
        state_manager=state_manager,
        ui_delegate=ui_delegate,
        message_handler=message_handler,
        tool_registry=tool_registry,
    )

    assert coordinator.message_processor.message_handler is message_handler
    assert coordinator.result_processor.tool_registry is tool_registry
    assert coordinator.ui_delegate is ui_delegate


@pytest.mark.asyncio
async def test_route_message_result_with_ui_delegate():
    """Test that _route_message_result delegates directly to result_processor using UI delegate."""
    state_manager = MagicMock()
    coordinator = MessageFlowCoordinator(state_manager)
    coordinator.chat_container = MagicMock()
    coordinator.result_processor.process_result = AsyncMock()

    ui_delegate = MagicMock(spec=ChatUIDelegate)
    result = {"type": "message", "content": "Hello"}
    core = MagicMock()

    await coordinator._route_message_result(
        result=result,
        ui_delegate=ui_delegate,
        core=core,
    )

    coordinator.result_processor.process_result.assert_awaited_once_with(
        result=result,
        container=coordinator.chat_container,
        core=core,
        ui_delegate=ui_delegate,
    )


@pytest.mark.asyncio
async def test_process_user_message_uses_direct_async_return():
    """Test that process_user_message consumes a direct return value from message_processor without callbacks."""
    state_manager = MagicMock()
    coordinator = MessageFlowCoordinator(state_manager)
    ui_delegate = MagicMock(spec=ChatUIDelegate)

    expected_result = {"type": "message", "content": "Direct reply"}
    coordinator.message_processor.send_message = AsyncMock(return_value=expected_result)
    coordinator._route_message_result = AsyncMock()

    await coordinator.process_user_message(
        message_text="Hello bot",
        ui_delegate=ui_delegate,
        core="test-core",
    )

    coordinator.message_processor.send_message.assert_awaited_once_with(
        message_text="Hello bot",
        ui_delegate=ui_delegate,
    )
    coordinator._route_message_result.assert_awaited_once_with(
        result=expected_result,
        ui_delegate=ui_delegate,
        core="test-core",
    )
    state_manager.set_processing.assert_called_with(False)


@pytest.mark.asyncio
async def test_process_user_message_skips_routing_when_result_none():
    """Test that process_user_message does not call routing when send_message returns None."""
    state_manager = MagicMock()
    coordinator = MessageFlowCoordinator(state_manager)
    ui_delegate = MagicMock(spec=ChatUIDelegate)

    coordinator.message_processor.send_message = AsyncMock(return_value=None)
    coordinator._route_message_result = AsyncMock()

    await coordinator.process_user_message(
        message_text="Hello bot",
        ui_delegate=ui_delegate,
    )

    coordinator.message_processor.send_message.assert_awaited_once()
    coordinator._route_message_result.assert_not_called()
    state_manager.set_processing.assert_called_with(False)


def test_coordinator_is_processing():
    state_manager = MagicMock()
    state_manager.is_processing = True
    coordinator = MessageFlowCoordinator(state_manager)
    assert coordinator.is_processing() is True

    state_manager.is_processing = False
    assert coordinator.is_processing() is False


def test_coordinator_set_message_handler():
    state_manager = MagicMock()
    coordinator = MessageFlowCoordinator(state_manager)
    new_handler = MagicMock()
    coordinator.set_message_handler(new_handler)
    assert coordinator.message_handler is new_handler


@pytest.mark.asyncio
async def test_coordinator_send_message_flow():
    state_manager = MagicMock()
    state_manager.conversation_id = "test-cid"
    message_handler = MagicMock()
    expected_result = {"type": "message", "content": "reply"}
    message_handler.handle_message = AsyncMock(return_value=expected_result)

    coordinator = MessageFlowCoordinator(
        state_manager=state_manager,
        message_handler=message_handler,
    )
    ui_delegate = MagicMock(spec=ChatUIDelegate)

    from unittest.mock import patch

    with patch(
        "frontend.pages.chatbot.message_flow_coordinator.DatabaseService.ensure_active_conversation",
        new_callable=AsyncMock,
    ), patch(
        "frontend.pages.chatbot.message_flow_coordinator.get_chat_history_db"
    ) as mock_db_getter:
        mock_db = MagicMock()
        mock_db.add_message = AsyncMock()
        mock_db_getter.return_value = mock_db

        result = await coordinator.send_message("hello", ui_delegate)

        assert result == expected_result
        state_manager.set_processing.assert_any_call(True)
        state_manager.set_input_enabled.assert_called_with(False)
        ui_delegate.update_status.assert_called_with("Processing message...")
        ui_delegate.add_message.assert_called_once()
        mock_db.add_message.assert_awaited_once()
        state_manager.clear_input.assert_called_once()
