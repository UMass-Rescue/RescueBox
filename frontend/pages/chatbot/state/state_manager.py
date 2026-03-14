"""
Chatbot State Manager

This module provides the ChatbotStateManager class for managing conversation state,
message history, and UI state in the chatbot interface.
"""

import logging
from typing import List, Optional
from frontend.pages.chatbot.chatbot_message import ChatMessage

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ChatbotStateManager:
    """
    Manages conversation state, message history, and UI state for the chatbot.

    This class centralizes all state management to avoid scattered state variables
    and provides a clean interface for state operations.

    Attributes:
        messages (List[ChatMessage]): List of chat messages in the conversation
        conversation_id (Optional[str]): Current conversation ID
        is_processing (bool): Whether a message is currently being processed
        status_text (str): Current status text to display
    """

    def __init__(self):
        """Initialize the state manager with default values."""
        self.messages: List[ChatMessage] = []
        self.conversation_id: Optional[str] = None
        self.is_processing = False
        self.status_text = "Ready"
        self.input_field = None  # Will be set by UI

        logger.debug("ChatbotStateManager initialized")

    def add_message(self, message: ChatMessage):
        """
        Add a message to the conversation history.

        Args:
            message (ChatMessage): Message to add
        """
        self.messages.append(message)
        logger.debug("Added message to conversation: %s", message.id)

    def clear_messages(self):
        """Clear all messages from the conversation."""
        self.messages.clear()
        logger.debug("Cleared all messages from conversation")

    def set_conversation_id(self, conversation_id: str):
        """
        Set the current conversation ID.

        Args:
            conversation_id (str): New conversation ID
        """
        self.conversation_id = conversation_id
        logger.debug("Set conversation ID: %s", conversation_id)

    def set_processing(self, processing: bool):
        """
        Set the processing state.

        Args:
            processing (bool): Whether processing is active
        """
        self.is_processing = processing
        status = "Processing..." if processing else "Ready"
        self.set_status(status)

    def set_status(self, text: str):
        """
        Set the status text.

        Args:
            text (str): Status text to display
        """
        self.status_text = text
        logger.debug("Status updated: %s", text)

    def get_messages(self) -> List[ChatMessage]:
        """
        Get all messages in the conversation.

        Returns:
            List[ChatMessage]: Copy of messages list
        """
        return self.messages.copy()

    def get_last_message(self) -> Optional[ChatMessage]:
        """
        Get the last message in the conversation.

        Returns:
            Optional[ChatMessage]: Last message or None if no messages
        """
        return self.messages[-1] if self.messages else None

    def set_input_field(self, input_field):
        """
        Set the input field reference for state management.

        Args:
            input_field: NiceGUI input field widget
        """
        self.input_field = input_field

    def clear_input(self):
        """Clear the input field if it exists."""
        if self.input_field:
            self.input_field.value = ""

    def reset_conversation(self):
        """Reset the conversation state for a new conversation."""
        self.clear_messages()
        self.conversation_id = None
        self.clear_input()
        self.set_status("New conversation started")
        logger.info("Conversation reset")

    def get_conversation_summary(self) -> dict:
        """
        Get a summary of the current conversation state.

        Returns:
            dict: Summary containing message count, conversation ID, etc.
        """
        return {
            'message_count': len(self.messages),
            'conversation_id': self.conversation_id,
            'is_processing': self.is_processing,
            'status': self.status_text,
            'has_messages': len(self.messages) > 0
        }
