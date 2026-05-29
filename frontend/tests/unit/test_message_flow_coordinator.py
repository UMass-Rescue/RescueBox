import pytest
from unittest.mock import AsyncMock, MagicMock

from frontend.pages.chatbot.handlers.message_flow_coordinator import MessageFlowCoordinator

@pytest.mark.asyncio
async def test_coordinator_creates_result_processor_callback():
    """Test that the coordinator correctly creates the result processor callback which resets processing state."""
    state_manager = MagicMock()
    coordinator = MessageFlowCoordinator(state_manager)
    
    input_field = MagicMock()
    is_processing_ref = {'value': True}
    add_message_func = MagicMock()
    show_error_func = MagicMock()
    update_status_func = MagicMock()
    core = MagicMock()
    
    # Create the callback
    process_result_cb = coordinator._create_result_processor(
        input_field, is_processing_ref, add_message_func, show_error_func, update_status_func, core
    )
    
    # Mock the routing method so we only test the callback wrapper
    coordinator._route_message_result = AsyncMock()
    
    result = {'type': 'message', 'content': 'Test'}
    await process_result_cb(result)
    
    # Verify routing was called
    coordinator._route_message_result.assert_called_once_with(
        result=result,
        input_field=input_field,
        is_processing_ref=is_processing_ref,
        add_message_func=add_message_func,
        show_error_func=show_error_func,
        update_status_func=update_status_func,
        core=core
    )
    
    # Verify processing state was reset after routing completed
    assert is_processing_ref['value'] is False
    state_manager.set_processing.assert_called_with(False)