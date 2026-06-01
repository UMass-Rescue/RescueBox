import pytest
from unittest.mock import MagicMock, patch

from frontend.pages.chatbot import ChatbotPage


@pytest.mark.asyncio
async def test_handle_new_conversation_resets_state_and_enables_input():
    """Test that starting a new conversation clears UI and securely enables the chat input."""
    with patch("frontend.pages.chatbot.ChatbotCore"), patch(
        "frontend.pages.chatbot.MessageHandler"
    ), patch("frontend.pages.chatbot.ToolRegistry"), patch(
        "frontend.pages.chatbot.ChatbotStateManager"
    ), patch(
        "frontend.pages.chatbot.MessageFlowCoordinator"
    ):

        page = ChatbotPage()
        page.state_manager = MagicMock()
        page.chat_container = MagicMock()
        page.below_input_area_container = MagicMock()

        with patch("frontend.components.chat.render_welcome_message") as mock_welcome:
            await page._handle_new_conversation()

            page.state_manager.reset_conversation.assert_called_once()
            page.chat_container.clear.assert_called_once()
            mock_welcome.assert_called_once_with(page.chat_container)
            page.state_manager.set_input_enabled.assert_called_once_with(True)
