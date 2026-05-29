"""
Chatbot State Manager

This module provides the ChatbotStateManager class for managing conversation state,
message history, and UI state in the chatbot interface.
"""

import logging
from typing import Any, List, Optional
from frontend.pages.chatbot.chatbot_message import ChatMessage

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Collapse the chat composer when input is "disabled" (pending form, processing, etc.).
# Uses a dedicated class so we do not remove Plugins mode's Tailwind `hidden` on the same element.
_INPUT_PENDING_HIDE_CLASS = "rb-chat-input-pending-only"


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
        self.input_area = None  # Optional: container with input_field + send_button

        logger.debug("ChatbotStateManager initialized")

    def attach_processing_strip(self, element: Any) -> None:
        """Show ``element`` only while :meth:`set_processing` is True (model call).

        Uses NiceGUI ``bind_visibility_from`` so updates propagate even though
        ``is_processing`` is a plain attribute (binding refresh polls the source).
        """
        element.bind_visibility_from(self, 'is_processing')

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

    def set_input_area(self, input_area):
        """
        Set the input area container (has input_field and send_button).
        Used by set_input_enabled to disable/enable both.

        Args:
            input_area: Container with .input_field and .send_button
        """
        self.input_area = input_area
        if input_area and not self.input_field:
            self.input_field = getattr(input_area, 'input_field', None)

    def set_input_enabled(self, enabled: bool):
        """
        Enable or disable the input area based on whether the system is ready for a new prompt.
        When disabled, the composer strip (textarea + send) is hidden (not greyed out) so the
        form / results flow is the only call to action. Forms appended under ``input_area`` stay
        visible (e.g. re-run after loading history). Plugins mode still uses ``hidden`` on the
        outer input area; this method toggles ``rb-chat-input-pending-only`` on the inner composer
        when available so both can compose safely.

        Args:
            enabled: True to show the composer and allow typing; False to hide and block input
        """
        try:
            area = self.input_area or (self.input_field and getattr(self.input_field, 'parent', None))
            # Hide only the textarea/send strip when present so forms rendered as siblings
            # inside ``input_area`` (e.g. re-run after loading chat history) remain visible.
            composer = (
                getattr(self.input_area, "composer_strip", None) if self.input_area else None
            )
            hide_target = composer or self.input_area or area
            if hide_target:
                if enabled:
                    hide_target.classes(remove=_INPUT_PENDING_HIDE_CLASS)
                else:
                    hide_target.classes(_INPUT_PENDING_HIDE_CLASS)
            if area:
                field = getattr(area, 'input_field', None) or self.input_field
                btn = getattr(area, 'send_button', None)
                if field:
                    (field.enable() if enabled else field.disable())
                if btn:
                    (btn.enable() if enabled else btn.disable())
            elif self.input_field:
                (self.input_field.enable() if enabled else self.input_field.disable())
        except Exception as e:
            logger.debug("Could not set input enabled=%s: %s", enabled, e)

    def clear_input(self):
        """Clear the input field if it exists."""
        if self.input_field:
            self.input_field.value = ""

    def reset_conversation(self):
        """Reset the conversation state for a new conversation."""
        self.clear_messages()
        self.conversation_id = None
        self.clear_input()
        self.is_processing = False
        self.set_status("Ready")
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
