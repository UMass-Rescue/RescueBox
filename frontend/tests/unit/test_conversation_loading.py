"""
Unit tests for conversation loading functionality.

Tests the "Load in Chat" feature that allows users to restore
conversations from history into the active chat interface.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from nicegui import app

# Import the modules we're testing
from frontend.utils.nicegui_storage import (
    set_conversation_to_load,
    get_conversation_to_load,
    clear_conversation_to_load
)
from frontend.pages.chatbot.chatbot import ChatbotPage
from frontend.components.chat.panels import load_conversation, rerun_tool_call
from frontend.database import ConversationRecord, ChatMessageRecord

# Test constants
TEST_CONVERSATION_ID = "conv-123"
TEST_CONVERSATION_DATA = {
    'title': 'Test Conversation',
    'created_at': '2024-01-01T10:00:00'
}
TEST_MESSAGES = [
    ChatMessageRecord(
        message_id='msg-1',
        conversation_id=TEST_CONVERSATION_ID,
        role='user',
        content='Hello, can you help me?',
        timestamp='2024-01-01T10:00:00Z'
    ),
    ChatMessageRecord(
        message_id='msg-2',
        conversation_id=TEST_CONVERSATION_ID,
        role='assistant',
        content='Yes, I can help you!',
        timestamp='2024-01-01T10:00:01Z'
    ),
    ChatMessageRecord(
        message_id='msg-3',
        conversation_id=TEST_CONVERSATION_ID,
        role='tool_call',
        content='',
        message_type='tool_call',
        tool_calls=[{'name': 'audio/transcribe', 'arguments': {'input_dir': '/tmp'}}],
        tool_call_endpoint='audio/transcribe',
        timestamp='2024-01-01T10:00:02Z'
    )
]


# Common test fixtures
@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        'conversation_id': TEST_CONVERSATION_ID,
        'conversation_data': TEST_CONVERSATION_DATA,
        'messages': TEST_MESSAGES
    }


@pytest.fixture
def mock_database():
    """Mock database with async methods."""
    mock_db = MagicMock()
    mock_db.get_conversation = AsyncMock(return_value={
        'title': 'Test Conversation',
        'created_at': '2024-01-01'
    })
    mock_db.get_messages = AsyncMock(return_value=[
        {'role': 'user', 'content': 'Hello'}
    ])
    return mock_db


@pytest.fixture
def mock_chatbot():
    """Mock chatbot instance."""
    chatbot = MagicMock(spec=ChatbotPage)
    chatbot.state_manager = MagicMock()
    chatbot.state_manager.conversation_id = TEST_CONVERSATION_ID
    return chatbot


@pytest.fixture
def mock_user_storage():
    """Fixture to mock nicegui.app.storage.user as a dictionary."""
    with patch('frontend.utils.nicegui_storage.app') as mock_app:
        mock_app.storage.user = {}
        yield mock_app.storage.user


class TestConversationStorage:
    """Test conversation storage functionality."""

    @pytest.fixture
    def chatbot(self):
        """Create a chatbot instance for testing."""
        with patch('nicegui.ui'):
            yield ChatbotPage()

    def test_set_conversation_to_load(self, mock_user_storage):
        """Test storing conversation data for loading."""
        test_messages = [
            {"message_id": "msg-1", "role": "user", "content": "Hello"},
            {"message_id": "msg-2", "role": "assistant", "content": "Hi there"}
        ]

        set_conversation_to_load(TEST_CONVERSATION_ID, TEST_CONVERSATION_DATA, test_messages)

        # Verify data is stored correctly
        stored = mock_user_storage.get('conversation_to_load')
        assert stored is not None
        assert stored['conversation_id'] == TEST_CONVERSATION_ID
        assert stored['conversation_data'] == TEST_CONVERSATION_DATA
        assert stored['messages'] == test_messages

    def test_get_conversation_to_load(self, mock_user_storage):
        """Test retrieving stored conversation data."""
        other_conversation_id = "conv-456"
        other_data = {"title": "Another Conversation"}
        other_messages = [{"role": "user", "content": "Test"}]

        set_conversation_to_load(other_conversation_id, other_data, other_messages)

        # Retrieve and verify data
        result = get_conversation_to_load()
        assert result is not None
        assert result['conversation_id'] == other_conversation_id
        assert result['conversation_data'] == other_data
        assert result['messages'] == other_messages

        # Verify data is cleared after retrieval
        assert get_conversation_to_load() is None

    def test_clear_conversation_to_load(self, mock_user_storage):
        """Test clearing stored conversation data."""
        set_conversation_to_load("test-conv", {"title": "Test"}, [{"content": "test"}])

        # Verify data exists
        assert mock_user_storage.get('conversation_to_load') is not None

        # Clear and verify
        clear_conversation_to_load()
        assert mock_user_storage.get('conversation_to_load') is None

    def test_get_empty_conversation_to_load(self, mock_user_storage):
        """Test retrieving when no conversation is stored."""
        clear_conversation_to_load()
        result = get_conversation_to_load()
        assert result is None

        # Verify storage is also empty
        assert mock_user_storage.get('conversation_to_load') is None


    @pytest.fixture
    def mock_chat_container(self):
        """Mock chat container for testing."""
        container = MagicMock()
        container.clear = MagicMock()
        return container

    @patch('frontend.utils.nicegui_storage.get_conversation_to_load')
    @pytest.mark.asyncio
    async def test_load_stored_conversation_success(self, mock_get_data, chatbot, sample_conversation_data, mock_chat_container):
        """Test successfully loading a stored conversation."""
        # Setup mocks
        mock_get_data.return_value = sample_conversation_data
        chatbot.chat_container = mock_chat_container

        # Mock UI operations to avoid slot errors
        with patch('frontend.pages.chatbot.chatbot.ui'), \
             patch('frontend.pages.chatbot.utils.conversation_loader.ui'):
            # Call the method
            await chatbot.load_conversation_from_data(sample_conversation_data)

        # Verify conversation was loaded via state manager
        assert chatbot.state_manager.conversation_id == 'conv-123'
        assert len(chatbot.state_manager.messages) == 3

        # Verify messages were added
        assert chatbot.state_manager.messages[0].role == 'user'
        assert chatbot.state_manager.messages[0].content == 'Hello, can you help me?'
        assert chatbot.state_manager.messages[1].role == 'assistant'
        assert chatbot.state_manager.messages[1].content == 'Yes, I can help you!'
        assert chatbot.state_manager.messages[2].role == 'tool_call'
        assert 'Tool call: audio/transcribe' in chatbot.state_manager.messages[2].content

        # Note: Container is not cleared - messages are appended to existing content
        # mock_chat_container.clear.assert_not_called()

    @patch('frontend.utils.nicegui_storage.get_conversation_to_load')
    @pytest.mark.asyncio
    async def test_load_stored_conversation_no_data(self, mock_get_data, chatbot):
        """Test loading when no conversation data is stored."""
        mock_get_data.return_value = None

        # Should not raise exception
        await chatbot.load_conversation_from_data({})

        # No changes should be made
        assert chatbot.state_manager.conversation_id is None
        assert chatbot.state_manager.messages == []

    @pytest.mark.asyncio
    @patch('frontend.utils.nicegui_storage.get_conversation_to_load')
    async def test_load_stored_conversation_invalid_data(self, mock_get_data, chatbot):
        """Test loading with invalid conversation data."""
        # Invalid data (missing required fields)
        mock_get_data.return_value = {'conversation_id': 'test'}

        # Mock UI operations to avoid slot errors
        with patch('frontend.pages.chatbot.chatbot.ChatMessage'), \
             patch('frontend.pages.chatbot.chatbot.ui'), \
             patch('frontend.pages.chatbot.utils.conversation_loader.ui'):
            # Should handle gracefully
            await chatbot.load_conversation_from_data({})

        # Should not crash, but may not load anything
        assert chatbot.state_manager.conversation_id is None


class TestLoadConversationIntegration:
    """Integration tests for the load conversation functionality."""

    @pytest.fixture
    def mock_chat_history(self):
        """Mock chat history database."""
        from unittest.mock import AsyncMock
        mock_db = MagicMock()

        # Mock conversation
        mock_conversation = ConversationRecord(
            conversation_id='conv-123',
            title='Test Conversation',
            created_at='2024-01-01T10:00:00',
            updated_at='2024-01-01T10:30:00'
        )

        # Mock messages
        mock_messages = [
            ChatMessageRecord(
                message_id='msg-1',
                conversation_id='conv-123',
                role='user',
                content='Hello',
                timestamp='2024-01-01T10:00:00Z'
            ),
            ChatMessageRecord(
                message_id='msg-2',
                conversation_id='conv-123',
                role='assistant',
                content='Hi there!',
                timestamp='2024-01-01T10:00:01Z'
            )
        ]

        # Set up async mock methods
        mock_db.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_db.get_messages = AsyncMock(return_value=mock_messages)

        return mock_db

    @pytest.mark.asyncio
    async def test_load_conversation_success(self):
        """load_conversation navigates with load_conversation= query param (full page reload)."""
        with patch(
            "frontend.components.chat.panels.conversation_actions.ui.navigate.to"
        ) as mock_nav:
            await load_conversation("conv-123")
        mock_nav.assert_called_once_with("/chatbot?load_conversation=conv-123")

    @pytest.mark.asyncio
    async def test_load_conversation_navigates_even_if_unknown_id(self):
        """Same navigation path regardless of DB state (page loads conversation)."""
        with patch(
            "frontend.components.chat.panels.conversation_actions.ui.navigate.to"
        ) as mock_nav:
            await load_conversation("nonexistent")
        mock_nav.assert_called_once_with("/chatbot?load_conversation=nonexistent")


class TestRerunFunctionality:
    """Test the rerun tool functionality."""

    @pytest.fixture
    def sample_tool_message(self):
        """Sample tool call message for testing."""
        return ChatMessageRecord(
            message_id='msg-123',
            conversation_id='conv-456',
            role='assistant',
            content='',
            message_type='tool_call',
            tool_calls=[{
                'name': 'audio/transcribe',
                'arguments': {'input_dir': '/tmp/audio', 'language': 'en'}
            }],
            tool_call_endpoint='audio/transcribe',
            tool_call_arguments={'input_dir': '/tmp/audio', 'language': 'en'},
            timestamp='2024-01-01T10:00:00Z'
        )

    @pytest.mark.asyncio
    @patch('frontend.database.get_chat_history_db')
    async def test_rerun_tool_call_success(self, mock_get_db, sample_tool_message):
        """Test rerunning a tool call successfully."""
        mock_db = MagicMock()
        mock_db.get_tool_call_by_id = AsyncMock(return_value=sample_tool_message)
        mock_get_db.return_value = mock_db

        with patch('frontend.components.chat.panels.conversation_actions.ui.navigate.to') as mock_navigate, \
             patch('frontend.components.chat.panels.conversation_actions.ui.notify') as mock_notify:

            await rerun_tool_call('msg-123')

            # Verify database call
            mock_db.get_tool_call_by_id.assert_called_once_with('msg-123')

            # Verify navigation with rerun parameter
            mock_navigate.assert_called_once_with('/chatbot?rerun=msg-123')

            # Verify notification
            mock_notify.assert_called_once_with('Re-running: audio/transcribe', type='info')

    @pytest.mark.asyncio
    @patch('frontend.database.get_chat_history_db')
    async def test_rerun_tool_call_not_found(self, mock_get_db):
        """Test rerunning a tool call that doesn't exist."""
        mock_db = MagicMock()
        mock_db.get_tool_call_by_id = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db

        with patch('frontend.components.chat.panels.conversation_actions.ui.notify') as mock_notify:
            await rerun_tool_call('nonexistent')

            mock_notify.assert_called_once_with('Tool call not found for rerun', type='negative')

    @pytest.mark.asyncio
    @patch('frontend.database.get_chat_history_db')
    async def test_rerun_tool_call_invalid_data(self, mock_get_db):
        """Test rerunning a tool call with invalid data."""
        # Create message with missing endpoint
        invalid_message = ChatMessageRecord(
            message_id='msg-456',
            conversation_id='conv-789',
            role='assistant',
            content='',
            message_type='tool_call',
            tool_calls=[{'name': 'unknown/tool'}],
            tool_call_endpoint=None,  # Missing endpoint
            timestamp='2024-01-01T10:00:00Z'
        )

        mock_db = MagicMock()
        mock_db.get_tool_call_by_id = AsyncMock(return_value=invalid_message)
        mock_get_db.return_value = mock_db

        with patch('frontend.components.chat.panels.conversation_actions.ui.notify') as mock_notify:
            await rerun_tool_call('msg-456')

            mock_notify.assert_called_once_with('Invalid tool call data for rerun', type='negative')


class TestChatbotPageRerun:
    """Test chatbot page rerun parameter handling."""

    @patch('frontend.pages.chatbot.parameter_handlers.get_chat_history_db')
    @pytest.mark.asyncio
    async def test_handle_rerun_parameter_success(self, mock_get_db):
        """Test handling rerun parameter successfully."""
        # Mock database and message
        from unittest.mock import AsyncMock
        mock_db = MagicMock()
        mock_message = ChatMessageRecord(
            message_id='msg-789',
            conversation_id='conv-999',
            role='assistant',
            content='',
            message_type='tool_call',
            tool_call_endpoint='audio/transcribe',
            tool_call_arguments={'input_dir': '/tmp'},
            timestamp='2024-01-01T10:00:00Z'
        )
        mock_db.get_tool_call_by_id = AsyncMock(return_value=mock_message)
        mock_get_db.return_value = mock_db

        # Mock ChatbotPage
        mock_chatbot = MagicMock()
        mock_chatbot.load_and_show_form = AsyncMock()

        # Import and call the function
        from frontend.pages.chatbot.parameter_handlers import handle_rerun_parameter

        with patch('frontend.pages.chatbot.parameter_handlers.ChatbotPage', return_value=mock_chatbot):
            with patch('frontend.pages.chatbot.parameter_handlers.ui.notify') as mock_notify:
                await handle_rerun_parameter('msg-789')

                # Verify database call
                mock_db.get_tool_call_by_id.assert_called_once_with('msg-789')

                # Verify ChatbotPage was created and load_and_show_form was called
                mock_chatbot.load_and_show_form.assert_called_once_with('audio/transcribe', {'input_dir': '/tmp'})

                # Verify notification
                mock_notify.assert_called_once_with('Re-running: audio/transcribe', type='info')

    @patch('frontend.pages.chatbot.parameter_handlers.get_chat_history_db')
    @pytest.mark.asyncio
    async def test_handle_rerun_parameter_not_found(self, mock_get_db):
        """Test handling rerun parameter for non-existent message."""
        from unittest.mock import AsyncMock
        mock_db = MagicMock()
        mock_db.get_tool_call_by_id = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db

        from frontend.pages.chatbot.parameter_handlers import handle_rerun_parameter

        with patch('frontend.pages.chatbot.parameter_handlers.ui.notify') as mock_notify:
            await handle_rerun_parameter('nonexistent')

            mock_notify.assert_called_once_with(
                'Tool call not found for rerun',
                type='negative'
            )


class TestErrorHandling:
    """Test error handling in conversation loading."""

    @patch("frontend.components.chat.panels.conversation_actions.ui.navigate.to")
    @patch("frontend.components.chat.panels.conversation_actions.ui.notify")
    @pytest.mark.asyncio
    async def test_load_conversation_navigation_error(self, mock_notify, mock_nav_to):
        """If navigate fails, user sees an error notification."""
        mock_nav_to.side_effect = Exception("Storage error")

        await load_conversation(TEST_CONVERSATION_ID)

        mock_notify.assert_called_with(
            "Error loading conversation: Storage error",
            type="negative",
        )

    @patch('frontend.utils.nicegui_storage.get_conversation_to_load')
    @pytest.mark.asyncio
    async def test_chatbot_load_message_error(self, mock_get_conversation, sample_conversation_data):
        """Test handling message loading errors in chatbot."""
        mock_get_conversation.return_value = sample_conversation_data

        # Create a partial mock - use real ChatbotPage but mock the problematic parts
        from frontend.pages.chatbot.chatbot import ChatbotPage

        with patch('frontend.pages.chatbot.utils.conversation_loader.ui.separator'), \
             patch('frontend.pages.chatbot.utils.conversation_loader.ui.label'), \
             patch('frontend.pages.chatbot.utils.message_service.ui.card') as mock_card, \
             patch('frontend.pages.chatbot.utils.message_service.ui.label'):

            # Mock the card context manager
            mock_card.return_value.__enter__ = MagicMock()
            mock_card.return_value.__exit__ = MagicMock()

            # Create a real ChatbotPage instance but with mocked UI components
            chatbot = ChatbotPage()
            # Mock the chat_container to avoid UI issues - make it a context manager that does nothing
            mock_container = MagicMock()
            mock_container.__enter__ = MagicMock(return_value=mock_container)
            mock_container.__exit__ = MagicMock(return_value=None)
            chatbot.chat_container = mock_container

            await chatbot.load_conversation_from_data(sample_conversation_data)

            # Verify conversation_id was still set despite message loading errors
            assert chatbot.state_manager.conversation_id == TEST_CONVERSATION_ID


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
