"""
Unit tests for chat history database functionality.

This module tests the complete chat history database operations that power
the RescueBox conversation management system. It validates the core database
functionality for storing, retrieving, and managing conversations and messages.

The tests cover all major database operations:
- Conversation lifecycle (creation, retrieval, deletion)
- Message management (adding user messages, tool calls, responses)
- Tool call history tracking and filtering
- Auto-generated conversation titles from user input
- Database integrity and relationship management
- Integration scenarios with multiple tool calls

The database operations are crucial for maintaining conversation state,
enabling users to review their interaction history, and supporting the
tool call execution workflow that powers RescueBox's AI capabilities.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from frontend.database.chat_history_db import (
    ChatHistoryDB,
    ConversationRecord,
    ChatMessageRecord,
    get_chat_history_db
)

# Test constants
TEST_CONVERSATION_TITLE = "Test Conversation"
FIRST_CONVERSATION_TITLE = "First"
SECOND_CONVERSATION_TITLE = "Second"

# Message content constants
USER_MESSAGE_CONTENT = "Find faces in images"
TOOL_CALL_CONTENT = "Selected tool: face-detection/findface"
FIRST_MESSAGE_CONTENT = "First message"
RESPONSE_CONTENT = "Response"
TOOL_CALL_MESSAGE_CONTENT = "Tool call"
MULTI_TOOL_MESSAGE_CONTENT = "Summarize photos and detect faces"

# Tool call constants
FACE_DETECTION_ENDPOINT = "face-detection/findface"
IMAGE_SUMMARY_ENDPOINT = "image_summary/summarize_images"
TOOL_CALL_INPUT_DIR = "/path/to/images"
TOOL_CALL_PATH_ARG = "/path"

# Message types
TEXT_MESSAGE_TYPE = "text"
TOOL_CALL_MESSAGE_TYPE = "tool_call"

# Roles
USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"

# Auto-generated title test
AUTO_TITLE_MESSAGE = "Find faces in my images"
AUTO_TITLE_FRAGMENT = "Find faces"


@pytest.fixture
def temp_db():
    """Create a temporary database for testing.

    Provides an isolated ChatHistoryDB instance with its own temporary
    database file. This ensures test isolation and prevents interference
    between different test cases. The database is properly cleaned up
    after each test.
    """
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / 'test_chat_history.db'
    db = ChatHistoryDB(db_path=db_path)
    db.connect()
    yield db
    db.close()
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


class TestChatHistoryDB:
    """Unit tests for ChatHistoryDB core functionality.

    This class validates the fundamental database operations that power
    the conversation management system. Each test focuses on a specific
    aspect of database functionality to ensure data integrity and correct
    behavior.

    Test coverage includes:
    - Conversation creation with and without custom titles
    - Message addition for different types (user, assistant, tool calls)
    - Message retrieval and ordering
    - Conversation listing and sorting
    - Tool call history tracking and filtering
    - Tool call retrieval by ID
    - Conversation deletion with cascade effects
    - Auto-generated titles from user messages

    All tests use isolated temporary databases to prevent interference
    and ensure reliable, repeatable results.
    """
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, temp_db):
        """Test creating a new conversation without custom title.

        Validates that conversations are created with all required fields
        properly initialized, including auto-generated IDs, timestamps,
        and zero message count for new conversations.
        """
        conversation = await temp_db.create_conversation()

        assert conversation.conversation_id is not None
        assert conversation.title is not None
        assert conversation.created_at is not None
        assert conversation.updated_at is not None
        assert conversation.message_count == 0

    @pytest.mark.asyncio
    async def test_create_conversation_with_title(self, temp_db):
        """Test creating a conversation with custom title.

        Ensures that conversations can be created with user-specified
        titles, overriding the default auto-generated title behavior.
        """
        conversation = await temp_db.create_conversation(title=TEST_CONVERSATION_TITLE)

        assert conversation.title == TEST_CONVERSATION_TITLE
    
    @pytest.mark.asyncio
    async def test_add_user_message(self, temp_db):
        """Test adding a user message to conversation.

        Validates that user messages are properly stored with correct
        metadata, and that the conversation's message count is updated
        to reflect the new message.
        """
        conversation = await temp_db.create_conversation()

        message = await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role=USER_ROLE,
            content=USER_MESSAGE_CONTENT
        )

        assert message.message_id is not None
        assert message.role == USER_ROLE
        assert message.content == USER_MESSAGE_CONTENT
        assert message.message_type == TEXT_MESSAGE_TYPE
        assert message.timestamp is not None

        # Verify conversation message count updated
        updated_conv = await temp_db.get_conversation(conversation.conversation_id)
        assert updated_conv.message_count == 1
    
    @pytest.mark.asyncio
    async def test_add_tool_call_message(self, temp_db):
        """Test adding a tool call message.

        Ensures that tool call messages are properly stored with all
        associated metadata, including endpoint information, arguments,
        and the complete tool call structure for execution tracking.
        """
        conversation = await temp_db.create_conversation()

        tool_call = {
            'name': FACE_DETECTION_ENDPOINT,
            'arguments': {'input_dir': TOOL_CALL_INPUT_DIR}
        }

        message = await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role=ASSISTANT_ROLE,
            content=TOOL_CALL_CONTENT,
            message_type=TOOL_CALL_MESSAGE_TYPE,
            tool_calls=[tool_call],
            tool_call_endpoint=FACE_DETECTION_ENDPOINT,
            tool_call_arguments={'input_dir': TOOL_CALL_INPUT_DIR}
        )

        assert message.message_type == TOOL_CALL_MESSAGE_TYPE
        assert message.tool_call_endpoint == FACE_DETECTION_ENDPOINT
        assert message.tool_call_arguments == {'input_dir': TOOL_CALL_INPUT_DIR}
        assert message.tool_calls == [tool_call]
    
    @pytest.mark.asyncio
    async def test_get_messages(self, temp_db):
        """Test retrieving messages for a conversation.

        Validates that messages are retrieved in the correct order
        (chronological) and contain all the expected metadata for
        both user and assistant messages.
        """
        conversation = await temp_db.create_conversation()

        # Add multiple messages
        await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role=USER_ROLE,
            content=FIRST_MESSAGE_CONTENT
        )
        await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role=ASSISTANT_ROLE,
            content=RESPONSE_CONTENT
        )

        messages = await temp_db.get_messages(conversation.conversation_id)

        assert len(messages) == 2
        assert messages[0].role == USER_ROLE
        assert messages[1].role == ASSISTANT_ROLE
    
    @pytest.mark.asyncio
    async def test_get_all_conversations(self, temp_db):
        """Test retrieving all conversations with proper ordering.

        Ensures that conversations are returned sorted by most recently
        updated first, which provides users with the most relevant and
        recent conversations at the top of their conversation list.
        """
        conv1 = await temp_db.create_conversation(title=FIRST_CONVERSATION_TITLE)
        conv2 = await temp_db.create_conversation(title=SECOND_CONVERSATION_TITLE)

        conversations = await temp_db.get_all_conversations()

        assert len(conversations) >= 2
        # Should be sorted by updated_at DESC (newest first)
        assert conversations[0].updated_at >= conversations[1].updated_at
    
    @pytest.mark.asyncio
    async def test_get_tool_call_history(self, temp_db):
        """Test retrieving tool call history"""
        conversation = await temp_db.create_conversation()
        
        await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role='assistant',
            content="Tool call",
            message_type='tool_call',
            tool_call_endpoint='face-detection/findface',
            tool_call_arguments={'input_dir': '/path'}
        )
        
        tool_calls = await temp_db.get_tool_call_history()
        
        assert len(tool_calls) >= 1
        assert tool_calls[0].tool_call_endpoint == 'face-detection/findface'
    
    @pytest.mark.asyncio
    async def test_get_tool_call_history_filtered(self, temp_db):
        """Test retrieving tool call history filtered by endpoint"""
        conversation = await temp_db.create_conversation()
        
        await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role='assistant',
            content="Tool call",
            message_type='tool_call',
            tool_call_endpoint='face-detection/findface',
            tool_call_arguments={}
        )
        
        tool_calls = await temp_db.get_tool_call_history(endpoint='face-detection/findface')
        
        assert len(tool_calls) >= 1
        assert all(tc.tool_call_endpoint == 'face-detection/findface' for tc in tool_calls)
    
    @pytest.mark.asyncio
    async def test_get_tool_call_by_id(self, temp_db):
        """Test retrieving a specific tool call by message ID"""
        conversation = await temp_db.create_conversation()
        
        message = await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role='assistant',
            content="Tool call",
            message_type='tool_call',
            tool_call_endpoint='face-detection/findface',
            tool_call_arguments={'input_dir': '/path'}
        )
        
        tool_call = await temp_db.get_tool_call_by_id(message.message_id)
        
        assert tool_call is not None
        assert tool_call.message_id == message.message_id
        assert tool_call.tool_call_endpoint == 'face-detection/findface'
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self, temp_db):
        """Test deleting a conversation"""
        conversation = await temp_db.create_conversation()
        
        # Add a message
        await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role='user',
            content="Test"
        )
        
        # Delete conversation
        success = await temp_db.delete_conversation(conversation.conversation_id)
        
        assert success is True
        
        # Verify conversation is deleted
        deleted_conv = await temp_db.get_conversation(conversation.conversation_id)
        assert deleted_conv is None
        
        # Verify messages are also deleted (CASCADE)
        messages = await temp_db.get_messages(conversation.conversation_id)
        assert len(messages) == 0
    
    @pytest.mark.asyncio
    async def test_auto_generate_title_from_first_message(self, temp_db):
        """Test that conversation title is auto-generated from first user message.

        Validates the intelligent title generation feature that creates
        meaningful conversation titles from the user's first message,
        improving conversation organization and discoverability.
        """
        conversation = await temp_db.create_conversation()

        # Add first user message
        await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role=USER_ROLE,
            content=AUTO_TITLE_MESSAGE
        )

        # Check if title was updated
        updated_conv = await temp_db.get_conversation(conversation.conversation_id)
        # Title should be generated from message (first 50 chars)
        assert AUTO_TITLE_FRAGMENT in updated_conv.title or updated_conv.title.startswith(AUTO_TITLE_FRAGMENT)


class TestChatHistoryDBIntegration:
    """Integration tests for complex chat history database scenarios.

    This class validates the database behavior in more complex, real-world
    scenarios that involve multiple tool calls, extended conversations,
    and comprehensive workflow testing.

    Test scenarios include:
    - Conversations with multiple sequential tool calls
    - Complex tool call history across different endpoints
    - End-to-end conversation workflows
    - Data consistency across related operations

    These integration tests ensure that the database correctly handles
    the complex interactions that occur during actual RescueBox usage,
    where users may invoke multiple tools in sequence or parallel.
    """
    
    @pytest.mark.asyncio
    async def test_conversation_with_multiple_tool_calls(self, temp_db):
        """Test a conversation with multiple tool calls.

        Validates the database's ability to handle complex conversations
        that involve multiple tool calls to different endpoints, ensuring
        proper tracking and retrieval of all tool call history.
        """
        conversation = await temp_db.create_conversation()

        # User message
        await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role=USER_ROLE,
            content=MULTI_TOOL_MESSAGE_CONTENT
        )
        
        # First tool call
        await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role='assistant',
            content="Selected tool: image_summary/summarize_images",
            message_type='tool_call',
            tool_call_endpoint='image_summary/summarize_images',
            tool_call_arguments={'input_dir': '/tmp'}
        )
        
        # Second tool call
        await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role='assistant',
            content="Selected tool: face-detection/findface",
            message_type='tool_call',
            tool_call_endpoint='face-detection/findface',
            tool_call_arguments={'input_dir': '/tmp'}
        )
        
        # Get all tool calls
        tool_calls = await temp_db.get_tool_call_history()
        
        assert len(tool_calls) >= 2
        endpoints = {tc.tool_call_endpoint for tc in tool_calls}
        assert 'image_summary/summarize_images' in endpoints
        assert 'face-detection/findface' in endpoints

