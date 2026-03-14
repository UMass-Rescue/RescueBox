"""
Conversation Manager.

Handles conversation creation, management, and message saving.
"""

import logging
from typing import Optional, Dict, Any

from frontend.pages.chatbot.utils.database_service import DatabaseService
from frontend.pages.chatbot.utils.message_service import MessageService
from frontend.database import get_chat_history_db


logger = logging.getLogger(__name__)


class ConversationManager:
    """Handles conversation creation, management, and message saving."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def ensure_conversation(self, endpoint: str, state_manager) -> Optional[str]:
        """
        Ensure we have a conversation for saving messages.

        Args:
            endpoint: API endpoint
            state_manager: State manager instance

        Returns:
            Conversation ID or None
        """
        conversation_id = state_manager.conversation_id

        if not conversation_id:
            self.logger.info("No conversation_id found, creating new conversation for tool: %s", endpoint)
            try:
                chat_history = get_chat_history_db()
                conversation = await chat_history.create_conversation(title=f"Tool: {endpoint}")
                conversation_id = conversation.conversation_id
                self.logger.info("Created new conversation %s with title 'Tool: %s'", conversation_id, endpoint)

                # Update state manager with new conversation_id
                state_manager.set_conversation_id(conversation_id)
                self.logger.info("Updated state manager with conversation_id: %s", conversation_id)

            except Exception as e:
                self.logger.error("Failed to create conversation for tool submission: %s", str(e))
                # Continue without conversation_id - messages won't be saved

        return conversation_id

    async def save_tool_call(self, conversation_id: str, request_body, endpoint: str):
        """
        Save tool call to conversation history.

        Args:
            conversation_id: Conversation ID
            request_body: Request body
            endpoint: API endpoint
        """
        if conversation_id:
            # Extract and serialize arguments
            arguments = {}
            if hasattr(request_body, 'inputs') and request_body.inputs:
                arguments = MessageService.serialize_arguments(request_body.inputs)
                self.logger.info("Extracted and serialized arguments: %s", arguments)

            # Save tool call using DatabaseService
            await DatabaseService.save_tool_call_to_history(conversation_id, endpoint, arguments)
