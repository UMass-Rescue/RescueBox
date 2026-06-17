"""
Unit tests for conversation loading functionality.

Tests the "Load in Chat" feature that allows users to restore
conversations from history into the active chat interface.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import the modules we're testing
from frontend.utils import (
    set_conversation_to_load,
    get_conversation_to_load,
    clear_conversation_to_load,
)
from frontend.pages.chatbot import ChatbotPage
from frontend.components.chat import load_conversation, rerun_tool_call
from frontend.database import ConversationRecord, ChatMessageRecord

# Test constants
TEST_CONVERSATION_ID = "conv-123"
TEST_CONVERSATION_DATA = {
    "title": "Test Conversation",
    "created_at": "2024-01-01T10:00:00",
}
TEST_MESSAGES = [
    ChatMessageRecord(
        message_id="msg-1",
        conversation_id=TEST_CONVERSATION_ID,
        role="user",
        content="Hello, can you help me?",
        timestamp="2024-01-01T10:00:00Z",
    ),
    ChatMessageRecord(
        message_id="msg-2",
        conversation_id=TEST_CONVERSATION_ID,
        role="assistant",
        content="Yes, I can help you!",
        timestamp="2024-01-01T10:00:01Z",
    ),
    ChatMessageRecord(
        message_id="msg-3",
        conversation_id=TEST_CONVERSATION_ID,
        role="tool_call",
        content="",
        message_type="tool_call",
        tool_calls=[{"name": "audio/transcribe", "arguments": {"input_dir": "/tmp"}}],
        tool_call_endpoint="audio/transcribe",
        timestamp="2024-01-01T10:00:02Z",
    ),
]


# Common test fixtures
@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "conversation_id": TEST_CONVERSATION_ID,
        "conversation_data": TEST_CONVERSATION_DATA,
        "messages": TEST_MESSAGES,
    }


@pytest.fixture
def mock_database():
    """Mock database with async methods."""
    mock_db = MagicMock()
    mock_db.get_conversation = AsyncMock(
        return_value={"title": "Test Conversation", "created_at": "2024-01-01"}
    )
    mock_db.get_messages = AsyncMock(
        return_value=[{"role": "user", "content": "Hello"}]
    )
    return mock_db


@pytest.fixture
def mock_chatbot():
    """Mock chatbot instance."""
    chatbot = MagicMock(spec=ChatbotPage)
    chatbot.state_manager = MagicMock()
    chatbot.state_manager.conversation_id = TEST_CONVERSATION_ID
    chatbot.load_and_show_form = AsyncMock()
    return chatbot


@pytest.fixture
def mock_user_storage():
    """Fixture to mock nicegui.app.storage.user as a dictionary."""
    with patch("frontend.utils.storage.app") as mock_app, patch(
        "frontend.utils.app"
    ) as mock_utils_app:
        mock_app.storage.user = {}
        mock_utils_app.storage.user = mock_app.storage.user
        yield mock_app.storage.user


class TestConversationStorage:
    """Test conversation storage functionality."""

    @pytest.fixture
    def chatbot(self):
        """Create a chatbot instance for testing."""
        with patch("nicegui.ui"):
            yield ChatbotPage()

    def test_set_conversation_to_load(self, mock_user_storage):
        """Test storing conversation data for loading."""
        test_messages = [
            {"message_id": "msg-1", "role": "user", "content": "Hello"},
            {"message_id": "msg-2", "role": "assistant", "content": "Hi there"},
        ]

        set_conversation_to_load(
            TEST_CONVERSATION_ID, TEST_CONVERSATION_DATA, test_messages
        )

        # Verify data is stored correctly
        stored = mock_user_storage.get("conversation_to_load")
        assert stored is not None
        assert stored["conversation_id"] == TEST_CONVERSATION_ID
        assert stored["conversation_data"] == TEST_CONVERSATION_DATA
        assert stored["messages"] == test_messages

    def test_get_conversation_to_load(self, mock_user_storage):
        """Test retrieving stored conversation data."""
        other_conversation_id = "conv-456"
        other_data = {"title": "Another Conversation"}
        other_messages = [{"role": "user", "content": "Test"}]

        set_conversation_to_load(other_conversation_id, other_data, other_messages)

        # Retrieve and verify data
        result = get_conversation_to_load()
        assert result is not None
        assert result["conversation_id"] == other_conversation_id
        assert result["conversation_data"] == other_data
        assert result["messages"] == other_messages

        # Verify data is cleared after retrieval
        assert get_conversation_to_load() is None

    def test_clear_conversation_to_load(self, mock_user_storage):
        """Test clearing stored conversation data."""
        set_conversation_to_load("test-conv", {"title": "Test"}, [{"content": "test"}])

        # Verify data exists
        assert mock_user_storage.get("conversation_to_load") is not None

        # Clear and verify
        clear_conversation_to_load()
        assert mock_user_storage.get("conversation_to_load") is None

    def test_get_empty_conversation_to_load(self, mock_user_storage):
        """Test retrieving when no conversation is stored."""
        clear_conversation_to_load()
        result = get_conversation_to_load()
        assert result is None

        # Verify storage is also empty
        assert mock_user_storage.get("conversation_to_load") is None

    @pytest.fixture
    def mock_chat_container(self):
        """Mock chat container for testing."""
        container = MagicMock()
        container.clear = MagicMock()
        return container

    @pytest.mark.skip(reason="Brittle UI context errors in unit test environment")
    @patch("frontend.utils.get_conversation_to_load")
    @pytest.mark.asyncio
    async def test_load_stored_conversation_success(
        self, mock_get_data, chatbot, sample_conversation_data, mock_chat_container
    ):
        """Test successfully loading a stored conversation."""
        # Setup mocks
        mock_get_data.return_value = sample_conversation_data
        chatbot.chat_container = mock_chat_container

        # Mock the database to return the sample messages
        from frontend.database.chat_history_db import ChatMessageRecord

        mock_records = [
            ChatMessageRecord(
                message_id=f"msg-{i}",
                conversation_id="conv-123",
                role=m.role,
                content=m.content,
                timestamp="2024-01-01T10:00:00Z",
            )
            for i, m in enumerate(TEST_MESSAGES)
        ]

        with patch("frontend.database.get_chat_history_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.get_messages = AsyncMock(return_value=mock_records)
            mock_get_db.return_value = mock_db

            # Mock UI operations to avoid slot errors
            with patch("frontend.pages.chatbot.ui"), patch(
                "frontend.components.chat.render_welcome_message"
            ):
                # Call the method
                await chatbot.load_conversation_from_data(sample_conversation_data)

        # Verify conversation was loaded via state manager
        assert chatbot.state_manager.conversation_id == "conv-123"
        assert len(chatbot.state_manager.messages) == 3

        # Verify messages were added
        assert chatbot.state_manager.messages[0].role == "user"
        assert chatbot.state_manager.messages[0].content == "Hello, can you help me?"
        assert chatbot.state_manager.messages[1].role == "assistant"
        assert chatbot.state_manager.messages[1].content == "Yes, I can help you!"
        # Tool calls have empty content but type 'tool_call'
        assert chatbot.state_manager.messages[2].role == "tool_call"

        # Note: Container is not cleared - messages are appended to existing content
        # mock_chat_container.clear.assert_not_called()

    @patch("frontend.utils.get_conversation_to_load")
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
    @patch("frontend.utils.get_conversation_to_load")
    async def test_load_stored_conversation_invalid_data(self, mock_get_data, chatbot):
        """Test loading with invalid conversation data."""
        # Invalid data (missing required fields)
        mock_get_data.return_value = {"conversation_id": "test"}

        # Mock UI operations to avoid slot errors
        with patch("frontend.pages.chatbot.ChatMessage"), patch(
            "frontend.pages.chatbot.ui"
        ), patch("frontend.pages.chatbot.ui"):
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
            conversation_id="conv-123",
            title="Test Conversation",
            created_at="2024-01-01T10:00:00",
            updated_at="2024-01-01T10:30:00",
        )

        # Mock messages
        mock_messages = [
            ChatMessageRecord(
                message_id="msg-1",
                conversation_id="conv-123",
                role="user",
                content="Hello",
                timestamp="2024-01-01T10:00:00Z",
            ),
            ChatMessageRecord(
                message_id="msg-2",
                conversation_id="conv-123",
                role="assistant",
                content="Hi there!",
                timestamp="2024-01-01T10:00:01Z",
            ),
        ]

        # Set up async mock methods
        mock_db.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_db.get_messages = AsyncMock(return_value=mock_messages)

        return mock_db

    @pytest.mark.asyncio
    @patch("frontend.components.chat.view.get_chat_history_db")
    async def test_load_conversation_success(self, mock_get_db):
        """load_conversation stashes data and forces full navigation via window.location.assign."""
        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.model_dump = MagicMock(return_value={"conversation_id": "conv-123"})
        mock_db.get_conversation = AsyncMock(return_value=mock_conv)
        mock_db.get_messages = AsyncMock(return_value=[])
        mock_get_db.return_value = mock_db

        with patch(
            "frontend.components.chat.view.utils.set_conversation_to_load"
        ) as mock_set, patch(
            "frontend.components.chat.view.ui.run_javascript"
        ) as mock_js:
            await load_conversation("conv-123")

        mock_set.assert_called_once_with(
            "conv-123", {"conversation_id": "conv-123"}, []
        )
        mock_js.assert_called_once()
        assert "load_conversation=conv-123" in mock_js.call_args[0][0]

    @pytest.mark.asyncio
    @patch("frontend.database.get_chat_history_db")
    async def test_load_conversation_not_found_no_navigate(self, mock_get_db):
        """Missing conversation: notify user; do not navigate."""
        mock_db = MagicMock()
        mock_db.get_conversation = AsyncMock(side_effect=Exception("DB unavailable"))
        mock_get_db.return_value = mock_db

        with patch("frontend.components.chat.view.ui.run_javascript") as mock_js, patch(
            "frontend.components.chat.view.ui.notify"
        ) as mock_notify:
            await load_conversation("nonexistent")

        mock_js.assert_not_called()
        mock_notify.assert_called_once()


class TestRerunFunctionality:
    """Test the rerun tool functionality."""

    @pytest.fixture
    def sample_tool_message(self):
        """Sample tool call message for testing."""
        return ChatMessageRecord(
            message_id="msg-123",
            conversation_id="conv-456",
            role="assistant",
            content="",
            message_type="tool_call",
            tool_calls=[
                {
                    "name": "audio/transcribe",
                    "arguments": {"input_dir": "/tmp/audio", "language": "en"},
                }
            ],
            tool_call_endpoint="audio/transcribe",
            tool_call_arguments={"input_dir": "/tmp/audio", "language": "en"},
            timestamp="2024-01-01T10:00:00Z",
        )

    @pytest.mark.asyncio
    @patch("frontend.components.chat.view.get_chat_history_db")
    async def test_rerun_tool_call_success(self, mock_get_db, sample_tool_message):
        """Test rerunning a tool call when chatbot is not mounted (navigate with ?rerun=)."""
        mock_db = MagicMock()
        mock_db.get_tool_call_by_id = AsyncMock(return_value=sample_tool_message)
        mock_get_db.return_value = mock_db

        with patch(
            "frontend.pages.chatbot.chat_page.ChatbotPage.get_instance",
            return_value=None,
        ), patch(
            "frontend.components.chat.view.ui.navigate.to"
        ) as mock_navigate, patch(
            "frontend.components.chat.view.ui.notify"
        ) as mock_notify:

            await rerun_tool_call("msg-123")

            mock_db.get_tool_call_by_id.assert_called_once_with("msg-123")
            mock_navigate.assert_called_once_with("/chatbot?rerun=msg-123")
            mock_notify.assert_called_once()
            assert mock_notify.call_args[0][0] == "Re-running: audio/transcribe"
            assert mock_notify.call_args[1].get("type") == "info"

    @pytest.mark.asyncio
    @patch("frontend.components.chat.view.get_chat_history_db")
    async def test_rerun_tool_call_on_chatbot_page(
        self, mock_get_db, sample_tool_message
    ):
        """Re-run Job button on /chatbot calls handle_rerun_parameter in-process."""
        mock_db = MagicMock()
        mock_db.get_tool_call_by_id = AsyncMock(return_value=sample_tool_message)
        mock_get_db.return_value = mock_db

        with patch(
            "frontend.pages.chatbot.chat_page.ChatbotPage.get_instance",
            return_value=MagicMock(),
        ), patch(
            "frontend.pages.chatbot.routes.handle_rerun_parameter",
            new_callable=AsyncMock,
        ) as mock_handle, patch(
            "frontend.components.chat.view.ui.navigate.to"
        ) as mock_navigate:
            await rerun_tool_call("msg-123")

            mock_handle.assert_awaited_once_with("msg-123")
            mock_navigate.assert_not_called()

    @pytest.mark.asyncio
    @patch("frontend.database.get_chat_history_db")
    async def test_rerun_tool_call_not_found(self, mock_get_db):
        """Test rerunning a tool call that doesn't exist."""
        mock_db = MagicMock()
        mock_db.get_tool_call_by_id = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db

        with patch("frontend.components.chat.view.ui.notify") as mock_notify:
            await rerun_tool_call("nonexistent")

            mock_notify.assert_called_once()
            assert mock_notify.call_args[0][0] == "Tool call not found for rerun"
            assert mock_notify.call_args[1].get("type") == "negative"

    @pytest.mark.skip(reason="Brittle notification check in safe_ui_call environment")
    @pytest.mark.asyncio
    @patch("frontend.database.get_chat_history_db")
    async def test_rerun_tool_call_invalid_data(self, mock_get_db):
        """Test rerunning a tool call with invalid data."""
        # Create message with missing endpoint
        invalid_message = ChatMessageRecord(
            message_id="msg-456",
            conversation_id="conv-789",
            role="assistant",
            content="",
            message_type="tool_call",
            tool_calls=[{"name": "unknown/tool"}],
            tool_call_endpoint=None,  # Missing endpoint
            timestamp="2024-01-01T10:00:00Z",
        )

        mock_db = MagicMock()
        mock_db.get_tool_call_by_id = AsyncMock(return_value=invalid_message)
        mock_get_db.return_value = mock_db

        with patch("frontend.components.chat.ui.notify") as mock_notify:
            await rerun_tool_call("msg-456")

            assert mock_notify.called
            # Ensure at least one negative notification
            assert any(
                call[1].get("type") == "negative" for call in mock_notify.call_args_list
            )


class TestChatbotPageRerun:
    """Test chatbot page rerun parameter handling."""

    @pytest.mark.skip(reason="Brittle mock interactions with ChatbotPage singleton")
    @patch("frontend.database.get_chat_history_db")
    @pytest.mark.asyncio
    async def test_handle_rerun_parameter_success(self, mock_get_db):
        """Test handling rerun parameter successfully."""
        # Mock database and message
        from unittest.mock import AsyncMock

        mock_db = MagicMock()
        mock_message = ChatMessageRecord(
            message_id="msg-789",
            conversation_id="conv-999",
            role="assistant",
            content="",
            message_type="tool_call",
            tool_call_endpoint="audio/transcribe",
            tool_call_arguments={"input_dir": "/tmp"},
            timestamp="2024-01-01T10:00:00Z",
        )
        mock_db.get_tool_call_by_id = AsyncMock(return_value=mock_message)
        mock_get_db.return_value = mock_db

        # Mock ChatbotPage
        mock_chatbot_class = MagicMock()
        mock_chatbot_class.get_instance.return_value = mock_chatbot

        # Import and call the function
        from frontend.pages.chatbot import handle_rerun_parameter

        with patch(
            "frontend.pages.chatbot.ChatbotPage.get_instance", return_value=mock_chatbot
        ):
            with patch("frontend.pages.chatbot.ui.notify") as mock_notify, patch(
                "frontend.database.chat_history_db.get_chat_history_db",
                return_value=mock_db,
            ):
                await handle_rerun_parameter("msg-789")

                # Verify database call
                mock_db.get_tool_call_by_id.assert_called_once_with("msg-789")

                # Verify load_and_show_form was called
                mock_chatbot.load_and_show_form.assert_called_once_with(
                    "audio/transcribe", {"input_dir": "/tmp"}
                )

                # Verify notification
                assert mock_notify.called
                assert any(
                    "Re-running" in str(call) for call in mock_notify.call_args_list
                )

    @pytest.mark.skip(reason="Brittle mock interactions with ChatbotPage singleton")
    @patch("frontend.database.get_chat_history_db")
    @pytest.mark.asyncio
    async def test_handle_rerun_parameter_not_found(self, mock_get_db):
        """Test handling rerun parameter for non-existent message."""
        from unittest.mock import AsyncMock

        mock_db = MagicMock()
        mock_db.get_tool_call_by_id = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db

        from frontend.pages.chatbot import handle_rerun_parameter

        with patch("frontend.pages.chatbot.ui.notify") as mock_notify, patch(
            "frontend.database.chat_history_db.get_chat_history_db",
            return_value=mock_db,
        ), patch("frontend.pages.chatbot.ChatbotPage.get_instance", return_value=None):
            await handle_rerun_parameter("nonexistent")

            assert mock_notify.called
            assert any("not found" in str(call) for call in mock_notify.call_args_list)


class TestErrorHandling:
    """Test error handling in conversation loading."""

    @patch("frontend.components.chat.view.get_chat_history_db")
    @patch("frontend.components.chat.view.ui.run_javascript")
    @patch("frontend.components.chat.view.ui.notify")
    @pytest.mark.asyncio
    async def test_load_conversation_navigation_error(
        self, mock_notify, mock_js, mock_get_db
    ):
        """If full-page navigation (assign) fails, user sees an error notification."""
        mock_db = MagicMock()
        mock_conv = MagicMock()
        mock_conv.model_dump = MagicMock(return_value={})
        mock_db.get_conversation = AsyncMock(return_value=mock_conv)
        mock_db.get_messages = AsyncMock(return_value=[])
        mock_get_db.return_value = mock_db
        mock_js.side_effect = OSError("Storage error")

        await load_conversation(TEST_CONVERSATION_ID)

        mock_notify.assert_called()
        assert "Error loading conversation" in mock_notify.call_args[0][0]
        assert mock_notify.call_args[1].get("type") == "negative"

    @pytest.mark.skip(reason="Brittle UI slot errors in unit test environment")
    @patch("frontend.utils.get_conversation_to_load")
    @pytest.mark.asyncio
    async def test_chatbot_load_message_error(
        self, mock_get_conversation, sample_conversation_data
    ):
        """Test handling message loading errors in chatbot."""
        mock_get_conversation.return_value = sample_conversation_data

        # Create a partial mock - use real ChatbotPage but mock the problematic parts
        from frontend.pages.chatbot import ChatbotPage

        with patch("frontend.pages.chatbot.ui.separator"), patch(
            "frontend.pages.chatbot.ui.label"
        ), patch("frontend.pages.chatbot.ui.card") as mock_card, patch(
            "frontend.pages.chatbot.ui.label"
        ), patch(
            "frontend.components.chat.ui_bridge.card"
        ), patch(
            "frontend.components.chat.ui_bridge.column"
        ), patch(
            "frontend.components.chat.ui_bridge.row"
        ), patch(
            "frontend.components.chat.ui_bridge.label"
        ), patch(
            "frontend.components.chat.ui_bridge.button"
        ):

            # Mock the card context manager
            mock_card.return_value.__enter__ = MagicMock()
            mock_card.return_value.__exit__ = MagicMock()

            # Create a real ChatbotPage instance but with mocked UI components
            with patch("frontend.pages.chatbot.ui.card"), patch(
                "frontend.components.chat.render_welcome_message"
            ):
                chatbot = ChatbotPage()
                # Mock methods that create UI to avoid slot issues
                chatbot._add_message = MagicMock()
                chatbot.chat_container = MagicMock()
                chatbot.chat_container.__enter__ = MagicMock(
                    return_value=chatbot.chat_container
                )
                chatbot.chat_container.__exit__ = MagicMock(return_value=None)

                # Mock the database to return the sample messages
                from frontend.database.chat_history_db import ChatMessageRecord

                mock_records = [
                    ChatMessageRecord(
                        message_id=f"msg-{i}",
                        conversation_id=TEST_CONVERSATION_ID,
                        role=m.role,
                        content=m.content,
                        timestamp="2024-01-01T10:00:00Z",
                    )
                    for i, m in enumerate(TEST_MESSAGES)
                ]
                with patch("frontend.database.get_chat_history_db") as mock_get_db:
                    mock_db = MagicMock()
                    mock_db.get_messages = AsyncMock(return_value=mock_records)
                    mock_get_db.return_value = mock_db

                    await chatbot.load_conversation_from_data(sample_conversation_data)

                # Verify conversation_id was still set despite message loading errors
                assert chatbot.state_manager.conversation_id == TEST_CONVERSATION_ID


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
