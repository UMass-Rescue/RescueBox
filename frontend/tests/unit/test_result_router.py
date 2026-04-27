import pytest
from unittest.mock import AsyncMock, MagicMock

from frontend.pages.chatbot.utils.result_router import ResultRouter

@pytest.mark.asyncio
async def test_route_message_result():
    router = ResultRouter()
    add_assistant_message_func = AsyncMock()
    show_error_func = AsyncMock()
    
    await router.route_result(
        result={'type': 'message', 'content': 'Hello'},
        chat_container=MagicMock(),
        tool_registry=MagicMock(),
        add_assistant_message_func=add_assistant_message_func,
        show_error_func=show_error_func,
        load_and_show_form_func=AsyncMock()
    )
    
    add_assistant_message_func.assert_called_once_with('Hello', 'assistant')
    show_error_func.assert_not_called()

@pytest.mark.asyncio
async def test_route_multi_tool_calls():
    router = ResultRouter()
    load_and_show_form_func = AsyncMock()
    
    tool_calls = [
        {'endpoint': 'tool1', 'arguments': {'a': 1}},
        {'endpoint': 'tool2', 'arguments': {'b': 2}}
    ]
    
    await router.route_result(
        result={'type': 'multi_tool_calls', 'tool_calls': tool_calls},
        chat_container=MagicMock(),
        tool_registry=MagicMock(),
        add_assistant_message_func=AsyncMock(),
        show_error_func=AsyncMock(),
        load_and_show_form_func=load_and_show_form_func
    )
    
    load_and_show_form_func.assert_called_once_with(
        'tool1',
        {'a': 1},
        remaining_calls=[{'endpoint': 'tool2', 'arguments': {'b': 2}}]
    )