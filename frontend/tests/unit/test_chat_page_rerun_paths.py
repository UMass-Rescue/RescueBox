from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from frontend.pages.chatbot.chat_page import ChatbotPage


@pytest.fixture
def chatbot_page_instance():
    with patch("frontend.pages.chatbot.chat_page.ChatbotCore"), patch(
        "frontend.pages.chatbot.chat_page.MessageHandler"
    ), patch("frontend.pages.chatbot.chat_page.ToolRegistry"), patch(
        "frontend.pages.chatbot.chat_page.ChatbotStateManager"
    ), patch(
        "frontend.pages.chatbot.chat_page.MessageFlowCoordinator"
    ):
        return ChatbotPage()


@pytest.mark.asyncio
async def test_handle_rerun_tool_prefers_tool_call_fields(chatbot_page_instance):
    msg = MagicMock()
    msg.tool_call_endpoint = "audio/transcribe"
    msg.tool_call_arguments = {"input_dir": "/tmp/a"}
    msg.metadata = {"endpoint": "wrong/endpoint", "arguments": {"x": 1}}

    with patch(
        "frontend.pages.chatbot.chat_page.get_chat_history_db"
    ) as mock_get_db, patch.object(
        chatbot_page_instance, "_re_run_tool", AsyncMock()
    ) as mock_rerun:
        mock_get_db.return_value.get_tool_call_by_id = AsyncMock(return_value=msg)
        await chatbot_page_instance.handle_rerun_tool("m1")

    mock_rerun.assert_awaited_once_with("audio/transcribe", {"input_dir": "/tmp/a"})


@pytest.mark.asyncio
async def test_handle_rerun_tool_falls_back_to_metadata(chatbot_page_instance):
    msg = MagicMock()
    msg.tool_call_endpoint = None
    msg.tool_call_arguments = None
    msg.metadata = {"endpoint": "image_summary/summarize-images", "arguments": {"a": 2}}

    with patch(
        "frontend.pages.chatbot.chat_page.get_chat_history_db"
    ) as mock_get_db, patch.object(
        chatbot_page_instance, "_re_run_tool", AsyncMock()
    ) as mock_rerun:
        mock_get_db.return_value.get_tool_call_by_id = AsyncMock(return_value=msg)
        await chatbot_page_instance.handle_rerun_tool("m2")

    mock_rerun.assert_awaited_once_with(
        "image_summary/summarize-images",
        {"a": 2},
    )


@pytest.mark.asyncio
async def test_handle_rerun_tool_warns_when_no_payload(chatbot_page_instance):
    msg = MagicMock()
    msg.tool_call_endpoint = None
    msg.tool_call_arguments = None
    msg.metadata = {}

    with patch(
        "frontend.pages.chatbot.chat_page.get_chat_history_db"
    ) as mock_get_db, patch(
        "frontend.pages.chatbot.chat_page.UIOperations.safe_notify"
    ) as mock_notify:
        mock_get_db.return_value.get_tool_call_by_id = AsyncMock(return_value=msg)
        await chatbot_page_instance.handle_rerun_tool("m3")

    mock_notify.assert_called_once()
