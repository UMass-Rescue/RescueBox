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
    - User messages: Blue background, right-aligned
    - Assistant messages: Gray background, left-aligned
    - Markdown is rendered for messages starting with '##'
    """
    logger.debug("Rendering message (ID: %s, role: %s)", message.id, message.role)
    try:
        from frontend.components.chat.message_card import render_message_card
        render_message_card(container, message.role, message.content, message.timestamp.strftime('%H:%M'))
    except Exception:
        # Fallback to inline rendering if component fails
        with container:
            alignment = 'items-end' if message.role == 'user' else 'items-start'
            bg_color = 'bg-blue-600 text-white' if message.role == 'user' else 'bg-gray-200'
            
            with ui.row().classes(f'w-full {alignment}'):
                with ui.card().classes(f'{bg_color} max-w-sm shadow-sm'):
                    with ui.row().classes('p-1.5 items-center gap-2 flex-wrap'):
                        if message.role == 'user':
                            ui.label('YOU:').classes('font-medium text-xs')
                        else:
                            ui.label('🤖 Assistant').classes('font-medium text-xs')

                        if message.content.startswith('##'):
                            ui.markdown(message.content).classes('text-sm')
                        else:
                            body_cls = 'text-sm'
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
    ui.notify(message, type='negative', position='top')

    # Create and render error message using extracted component when available
    try:
        from frontend.components.errors.error_display import render_error_message
        render_error_message(container, f'Error: {message}')
    except Exception:
        # Fallback: create and render error message
        error_msg = ChatMessage('assistant', f'❌ Error: {message}')
        render_message(container, error_msg)
