"""
Chatbot Message Components

This module provides the ChatMessage data class and message rendering/display
functionality for the chatbot interface.
"""

import logging
from nicegui import ui
from typing import Optional
from datetime import datetime
import uuid

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ChatMessage:
    """
    Chat message data class.
    
    Represents a single message in the chat conversation with role, content,
    type, metadata, and timestamp.
    
    Attributes:
        id (str): Unique message identifier (UUID)
        role (str): Message role ('user' or 'assistant')
        content (str): Message content/text
        type (str): Message type ('text', 'form', 'results', etc.)
        metadata (dict): Additional message metadata
        timestamp (datetime): Message timestamp
    """
    
    def __init__(self, role: str, content: str, message_type: str = 'text', metadata: Optional[dict] = None):
        """
        Initialize ChatMessage.
        
        Args:
            role (str): Message role ('user' or 'assistant')
            content (str): Message content/text
            message_type (str): Message type. Defaults to 'text'
            metadata (Optional[dict]): Additional metadata. Defaults to None
        """
        logger.debug("Creating chat message (role: %s, type: %s)", role, message_type)
        self.id = str(uuid.uuid4())
        self.role = role
        self.content = content
        self.type = message_type
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        logger.debug("Chat message created with ID: %s", self.id)


def render_message(container: ui.element, message: ChatMessage):
    """
    Render a message in the chat container.
    
    Displays message with appropriate styling based on role (user/assistant).
    Supports markdown rendering for messages starting with '##'.
    
    Args:
        container (ui.element): Chat container to render message in
        message (ChatMessage): Message to render
    
    Returns:
        None
    
    Tips:
    - User messages: White bubble, right-aligned
    - Assistant messages: Gray background, left-aligned
    - Assistant messages starting with '##' are rendered as markdown; user messages are plain text.
    """
    logger.debug("Rendering message (ID: %s, role: %s)", message.id, message.role)
    try:
        from frontend.components.chat.message_card import render_message_card
        render_message_card(container, message.role, message.content, message.timestamp.strftime('%H:%M'))
    except Exception:
        # Fallback to inline rendering if component fails
        from frontend.components.chat.message_card import (
            ASSISTANT_MARKDOWN_CLASSES,
            ASSISTANT_PLAIN_CLASSES,
            USER_PLAIN_CLASSES,
        )
        from frontend.design_tokens import Design

        with container:
            alignment = "items-end" if message.role == "user" else "items-start"
            bubble = (
                Design.CHAT_USER_BUBBLE
                if message.role == "user"
                else Design.CHAT_ASSISTANT_BUBBLE
            )

            with ui.row().classes(f"w-full {alignment}"):
                with ui.card().classes(f"{bubble} max-w-sm"):
                    with ui.row().classes("p-1.5 items-center gap-2 flex-wrap"):
                        if message.role == "user":
                            ui.label("YOU:").classes(Design.CHAT_USER_LABEL)
                        else:
                            ui.label("Assistant").classes(
                                "font-medium !text-sm sm:!text-base text-zinc-600"
                            )

                        if message.content.startswith('##') and message.role != 'user':
                            ui.markdown(message.content).classes(ASSISTANT_MARKDOWN_CLASSES)
                        else:
                            body_cls = (
                                ASSISTANT_PLAIN_CLASSES
                                if message.role != 'user'
                                else USER_PLAIN_CLASSES
                            )
                            if '\n' in (message.content or ''):
                                body_cls += ' whitespace-pre-line'
                            ui.label(message.content).classes(body_cls)
                        ui.label(message.timestamp.strftime('%H:%M')).classes('text-xs opacity-70')

    logger.debug("Message rendered successfully")


def show_error_message(container: ui.element, message: str):
    """
    Show error notification and assistant message.
    
    Displays error as both a notification and an assistant message in the chat.
    
    Args:
        container (ui.element): Chat container to display error in
        message (str): Error message text
    
    Returns:
        None
    
    Tips:
    - Shows both UI notification and chat message for visibility
    - Error messages use assistant role styling
    """
    logger.error("Showing error message: %s", message)
    ui.notify(message, type='negative', position='top', classes='rb-notify-505759')

    # Create and render error message using extracted component when available
    try:
        from frontend.components.errors.error_display import render_error_message
        render_error_message(container, f'Error: {message}')
    except Exception:
        # Fallback: create and render error message
        error_msg = ChatMessage('assistant', f'Error: {message}')
        render_message(container, error_msg)
