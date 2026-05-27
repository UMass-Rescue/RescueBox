"""Unit tests for chat history database with NiceGUI storage integration

Note: Some tests in this file test expected behavior for future user_id support.
These tests may need to be updated once user_id is added to the database schema.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from frontend.database.chat_history_db import (
    ChatHistoryDB,
    ChatMessageRecord,
    get_chat_history_db
)
from frontend.utils import get_user_id


class TestChatHistoryNiceGUIIntegration:
    """Tests for chat history database integration with NiceGUI storage"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / 'test_chat_history.db'
        db = ChatHistoryDB(db_path=db_path)
        db.connect()
        yield db
        db.close()
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_conversation_persistence_basic(self, temp_db):
        """Test that conversations persist in database (basic functionality)"""
        conversation = await temp_db.create_conversation()
        
        assert conversation.conversation_id is not None
        
        # Verify conversation can be retrieved
        retrieved = await temp_db.get_conversation(conversation.conversation_id)
        assert retrieved is not None
        assert retrieved.conversation_id == conversation.conversation_id
    
    @pytest.mark.asyncio
    async def test_get_all_conversations(self, temp_db):
        """Test getting all conversations (current implementation)"""
        conv1 = await temp_db.create_conversation(title="First")
        conv2 = await temp_db.create_conversation(title="Second")
        
        # Get all conversations (no filter - current implementation)
        all_convs = await temp_db.get_all_conversations()
        all_conv_ids = {c.conversation_id for c in all_convs}
        
        assert conv1.conversation_id in all_conv_ids
        assert conv2.conversation_id in all_conv_ids
    
    @pytest.mark.asyncio
    async def test_message_saved_to_conversation(self, temp_db):
        """Test that messages are saved and associated with conversation"""
        conversation = await temp_db.create_conversation()
        
        message = await temp_db.add_message(
            conversation_id=conversation.conversation_id,
            role='user',
            content="Test message"
        )
        
        # Verify message is associated with conversation
        messages = await temp_db.get_messages(conversation.conversation_id)
        assert len(messages) == 1
        assert messages[0].message_id == message.message_id
        assert messages[0].content == "Test message"
        
        # Verify conversation message count updated
        updated_conv = await temp_db.get_conversation(conversation.conversation_id)
        assert updated_conv.message_count == 1

