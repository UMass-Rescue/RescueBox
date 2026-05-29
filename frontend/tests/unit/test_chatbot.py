import pytest
from unittest.mock import MagicMock, patch

from frontend.pages.chatbot.chatbot import ChatbotPage

@pytest.mark.asyncio
async def test_handle_new_conversation_resets_state_and_enables_input():
    """Test that starting a new conversation clears UI and securely enables the chat input."""
    with patch('frontend.pages.chatbot.chatbot.ChatbotCore'), \
         patch('frontend.pages.chatbot.chatbot.MessageHandler'), \
         patch('frontend.pages.chatbot.chatbot.ToolRegistry'), \
         patch('frontend.pages.chatbot.chatbot.ChatbotStateManager'), \
         patch('frontend.pages.chatbot.chatbot.ChatbotEventHandler'), \
         patch('frontend.pages.chatbot.chatbot.CallbackManager'), \
         patch('frontend.pages.chatbot.chatbot.ConversationLoader'), \
         patch('frontend.pages.chatbot.chatbot.MessageFlowCoordinator'):
         
        page = ChatbotPage()
        page.state_manager = MagicMock()
        page.chat_container = MagicMock()
        page.below_input_area_container = MagicMock()
        
        with patch('frontend.components.chat.chat_window.render_welcome_message') as mock_welcome:
            await page._handle_new_conversation()
            
            page.state_manager.reset_conversation.assert_called_once()
            page.chat_container.clear.assert_called_once()
            mock_welcome.assert_called_once_with(page.chat_container)
            page.state_manager.set_input_enabled.assert_called_once_with(True)