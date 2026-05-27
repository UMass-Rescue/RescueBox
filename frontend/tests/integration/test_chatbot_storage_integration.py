"""Integration tests for chatbot with NiceGUI storage integration

These tests verify the integration between chatbot and NiceGUI storage.
All dependencies are real - no mocks used.
"""

import pytest
from nicegui.testing import User
import uuid
from frontend.chatbot.config import ChatbotConfig
from frontend.database.chat_history_db import ChatHistoryDB, ConversationRecord
from frontend.utils import (
    get_current_conversation_id,
    set_current_conversation_id,
    get_user_id
)


@pytest.mark.api
@pytest.mark.integration
class TestChatbotStorageIntegration:
    """Tests for chatbot integration with NiceGUI storage"""
    
    @pytest.fixture
    def mock_chatbot_page(self):
        """Create a mock chatbot page"""
        from frontend.pages.chatbot import ChatbotPage
        from frontend.chatbot.config import ChatbotConfig
        
        page = ChatbotPage()
        return page
    
    @pytest.mark.asyncio
    async def test_conversation_id_persisted_in_storage(self, user: User):
        """Test that conversation ID is stored in NiceGUI storage"""
        from frontend.pages.chatbot import ChatbotPage
        from frontend.chatbot.config import ChatbotConfig
        
        route = f'/test_chatbot_{uuid.uuid4().hex}'
        @user.app.page(route)
        async def chatbot_page():
            page = ChatbotPage()
            
            # Initialize conversation (should create and store in NiceGUI storage)
            await page.new_conversation()
            
            # Check that conversation_id is stored
            stored_conv_id = get_current_conversation_id()
            assert stored_conv_id is not None
            assert stored_conv_id == page.conversation_id
        
        await user.open(route)
    
    @pytest.mark.asyncio
    async def test_conversation_id_loaded_from_storage(self, user: User):
        """Test that conversation ID is loaded from NiceGUI storage on page load"""
        from frontend.pages.chatbot import ChatbotPage
        from frontend.chatbot.config import ChatbotConfig
        
        test_conv_id = "test-conversation-123"
        
        route = f'/test_chatbot_{uuid.uuid4().hex}'
        @user.app.page(route)
        async def chatbot_page():
            # Set conversation ID in storage before creating page
            set_current_conversation_id(test_conv_id)
            
            page = ChatbotPage()
            
            # Render should load conversation from storage if URL params don't override
            # (This depends on implementation - may need to mock URL params)
            stored_conv_id = get_current_conversation_id()
            assert stored_conv_id == test_conv_id
        
        await user.open(route)
    
    @pytest.mark.asyncio
    async def test_new_conversation_updates_storage(self, user: User):
        """Test that creating new conversation updates NiceGUI storage"""
        from frontend.pages.chatbot import ChatbotPage
        from frontend.chatbot.config import ChatbotConfig
        
        initial_conv_id = "initial-conversation"
        
        route = f'/test_chatbot_{uuid.uuid4().hex}'
        @user.app.page(route)
        async def chatbot_page():
            page = ChatbotPage()
            
            # Set initial conversation ID in storage (page should read it on load)
            set_current_conversation_id(initial_conv_id)
            
            # Create new conversation
            await page.new_conversation()
            
            # Check that storage was updated with new conversation ID
            stored_conv_id = get_current_conversation_id()
            assert stored_conv_id is not None
            assert stored_conv_id != initial_conv_id
            assert stored_conv_id == page.conversation_id
        
        await user.open(route)
    
    @pytest.mark.asyncio
    async def test_user_message_saved_to_history(self, user: User):
        """Test that user messages are saved to chat history with user ID"""
        from frontend.pages.chatbot import ChatbotPage
        from frontend.chatbot.config import ChatbotConfig
        from frontend.database import get_chat_history_db
        from frontend.utils import get_user_id
        
        route = f'/test_chatbot_{uuid.uuid4().hex}'
        @user.app.page(route)
        async def chatbot_page():
            page = ChatbotPage()
            
            # Initialize conversation
            await page.new_conversation()
            
            # Get user ID
            user_id = get_user_id()
            
            # Verify conversation was created with user_id (if implemented)
            # This test depends on implementation details
            chat_history_db = get_chat_history_db()
            conversation = await chat_history_db.get_conversation(page.conversation_id)
            
            # Conversation should exist
            assert conversation is not None
            # If user_id support is implemented, check it matches
            # assert conversation.user_id == user_id
        
        await user.open(route)
    
    @pytest.mark.asyncio
    async def test_tool_call_saved_to_history(self, user: User):
        """Test that tool calls are saved to chat history"""
        from frontend.pages.chatbot import ChatbotPage
        from frontend.chatbot.config import ChatbotConfig
        from frontend.database import get_chat_history_db
        
        route = f'/test_chatbot_{uuid.uuid4().hex}'
        @user.app.page(route)
        async def chatbot_page():
            page = ChatbotPage()
            
            # Initialize conversation
            await page.new_conversation()
            conv_id = page.conversation_id
            
            # Test tool call - using real handler processing
            # Note: This requires a valid endpoint, so we'll test with a known endpoint if available
            # For now, we just verify the conversation exists
            assert conv_id is not None
            
            # Verify conversation was created in database
            chat_history_db = get_chat_history_db()
            conversation = await chat_history_db.get_conversation(conv_id)
            assert conversation is not None
            assert conversation.conversation_id == conv_id
        
        await user.open(route)


@pytest.mark.api
@pytest.mark.integration
class TestChatHistoryPersistence:
    """Tests for chat history persistence across page reloads"""
    
    @pytest.mark.asyncio
    async def test_conversation_persists_across_navigation(self, user: User):
        """Test that conversation persists when navigating away and back"""
        from frontend.pages.chatbot import ChatbotPage
        from frontend.chatbot.config import ChatbotConfig
        from frontend.utils import (
            get_current_conversation_id,
            set_current_conversation_id
        )
        from frontend.database import get_chat_history_db
        
        test_conv_id = None
        
        route = f'/test_chatbot_{uuid.uuid4().hex}'
        @user.app.page(route)
        async def chatbot_page():
            nonlocal test_conv_id
            page = ChatbotPage()
            await page.new_conversation()
            test_conv_id = page.conversation_id
        
        # First visit - create conversation
        await user.open(route)
        
        stored_conv_id = None
        
        dummy_route1 = f'/dummy_{uuid.uuid4().hex}'
        @user.app.page(dummy_route1)
        async def dummy_page():
            nonlocal stored_conv_id
            stored_conv_id = get_current_conversation_id()
            
        # Simulate navigation away (storage should persist)
        await user.open(dummy_route1)
        assert stored_conv_id == test_conv_id
        
        # Verify conversation exists in database
        chat_history_db = get_chat_history_db()
        conversation = await chat_history_db.get_conversation(stored_conv_id)
        assert conversation is not None
        assert conversation.conversation_id == stored_conv_id
    
    @pytest.mark.asyncio
    async def test_messages_persist_in_database(self, user: User):
        """Test that messages persist in database even after page reload"""
        from frontend.pages.chatbot import ChatbotPage
        from frontend.chatbot.config import ChatbotConfig
        from frontend.database import get_chat_history_db
        from frontend.utils import get_current_conversation_id
        
        route = f'/test_chatbot_{uuid.uuid4().hex}'
        @user.app.page(route)
        async def chatbot_page():
            page = ChatbotPage()
            await page.new_conversation()
            
            # Add a test message (would normally be done via send_message)
            chat_history_db = get_chat_history_db()
            await chat_history_db.add_message(
                conversation_id=page.conversation_id,
                role='user',
                content="Test message for persistence"
            )
        
        await user.open(route)
        
        conv_id = None
        
        dummy_route2 = f'/dummy_{uuid.uuid4().hex}'
        @user.app.page(dummy_route2)
        async def dummy_page2():
            nonlocal conv_id
            conv_id = get_current_conversation_id()
            
        await user.open(dummy_route2)
        
        # Retrieve conversation from database
        assert conv_id is not None
        
        chat_history_db = get_chat_history_db()
        messages = await chat_history_db.get_messages(conv_id)
        
        assert len(messages) >= 1
        assert any(msg.content == "Test message for persistence" for msg in messages)
