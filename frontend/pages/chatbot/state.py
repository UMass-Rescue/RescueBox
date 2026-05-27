from __future__ import annotations
import logging
from typing import Callable, List, Optional, Any, Dict
from enum import Enum
from dataclasses import dataclass

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Represents a single message in the chat history."""
    role: MessageRole | str
    content: str
    id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    message_type: str = "text"

# Collapse the chat composer when input is "disabled" (pending form, processing, etc.).
# Uses a dedicated class so we do not remove Plugins mode's Tailwind `hidden` on the same element.
_INPUT_PENDING_HIDE_CLASS = "rb-chat-input-pending-only"

class ChatbotStateManager:
    """Manages conversation state, message history, and UI state for the chatbot."""

    def __init__(self):
        """Initialize the state manager with default values."""
        self.messages: List[ChatMessage] = []
        self.conversation_id: Optional[str] = None
        self.is_processing = False
        self.status_text = "Ready"
        self.input_field = None
        self.input_area = None

        logger.debug("ChatbotStateManager initialized")

    def attach_processing_strip(self, element: Any) -> None:
        """Show ``element`` only while :meth:`set_processing` is True (model call)."""
        element.bind_visibility_from(self, 'is_processing')

    def add_message(self, message: ChatMessage):
        """Add a message to the conversation history."""
        self.messages.append(message)
        logger.debug("Added message to conversation: %s", message.id)

    def clear_messages(self):
        """Clear all messages from the conversation."""
        self.messages.clear()
        logger.debug("Cleared all messages from conversation")

    def set_conversation_id(self, conversation_id: str):
        """Set the current conversation ID."""
        self.conversation_id = conversation_id
        logger.debug("Set conversation ID: %s", conversation_id)

    def set_processing(self, processing: bool, hide_input: bool = True):
        """
        Set the processing state.
        
        Args:
            processing: Whether the system is processing.
            hide_input: If True, the input area is hidden (Stage 2).
                        If False, it is only greyed out (Stage 1/Normal Chat).
        """
        self.is_processing = processing
        status = "Processing..." if processing else "Ready"
        self.set_status(status)
        # Apply the desired input area state
        self.set_input_enabled(not processing, hide_completely=(processing and hide_input))

    def set_status(self, text: str):
        """Set the status text."""
        self.status_text = text
        logger.debug("Status updated: %s", text)

    def get_messages(self) -> List[ChatMessage]:
        """Get all messages in the conversation."""
        return self.messages.copy()

    def get_last_message(self) -> Optional[ChatMessage]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None

    def set_input_field(self, input_field):
        """Set the input field reference for state management."""
        self.input_field = input_field

    def set_input_area(self, input_area):
        """Set the input area container (has input_field and send_button)."""
        self.input_area = input_area
        if input_area and not self.input_field:
            self.input_field = getattr(input_area, 'input_field', None)

    def set_input_enabled(self, enabled: bool, hide_completely: bool = False):
        """
        Enable or disable the input area.
        
        Args:
            enabled: Whether input is allowed.
            hide_completely: If True and enabled is False, the area is hidden (Stage 2).
                             If False and enabled is False, it is greyed out (Stage 1).
        """
        try:
            from nicegui import ui
            area = self.input_area or (self.input_field and getattr(self.input_field, 'parent', None))
            composer = (
                getattr(self.input_area, "composer_strip", None) if self.input_area else None
            )
            hide_target = composer or self.input_area or area
            if hide_target:
                # Stage 1: Grey out (pending-only class)
                # Stage 2: Remove/Hide completely (Tailwind hidden)
                if enabled:
                    hide_target.classes(remove=f"{_INPUT_PENDING_HIDE_CLASS} hidden")
                else:
                    if hide_completely:
                        hide_target.classes("hidden").classes(remove=_INPUT_PENDING_HIDE_CLASS)
                    else:
                        hide_target.classes(_INPUT_PENDING_HIDE_CLASS).classes(remove="hidden")
            
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
        """Get a summary of the current conversation state."""
        return {
            'message_count': len(self.messages),
            'conversation_id': self.conversation_id,
            'is_processing': self.is_processing,
            'status': self.status_text,
            'has_messages': len(self.messages) > 0
        }

@dataclass
class MessageSendParams:
    """Arguments for MessageSender."""
    message_text: str
    input_field: Any
    is_processing_ref: Dict[str, Any]
    message_handler: Any
    process_handler_result_func: Callable[..., Any]
    add_message_func: Callable[..., Any]
    show_error_func: Callable[..., Any]
    update_status_func: Callable[..., Any]
    conversation_id_ref: Optional[Dict[str, Any]] = None
