"""
Chatbot UI Components

This module provides UI layout and rendering functions for the chatbot interface,
including the main layout, input area, and status bar.
"""

import logging
from nicegui import ui
from typing import Callable

# Import common utilities
from frontend.pages.chatbot.utils import UIStyling, ChatUIBuilder

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_chat_ui(
    on_send: Callable,
    on_new_conversation: Callable,
    tool_registry,  # Tool registry for direct tool picker access
    core,  # Chatbot core for form loading
    form_submit_handler,  # Form submit handler
    status_text_ref: object = None,
    state_manager=None,  # ChatbotStateManager for clearing when switching modes
) -> tuple[ui.element, ui.textarea, ui.label]:
    """
    Create the chatbot UI layout with chat-intuitive design.

    Creates a modern chat-like interface using the ChatUIBuilder for proper
    separation of concerns and maintainability.

    Args:
        on_send (Callable): Callback for send button/action
        on_new_conversation (Callable): Callback for new conversation button
        tool_registry: Tool registry for direct tool picker access
        core: Chatbot core for form loading
        form_submit_handler: Form submit handler
        status_text_ref (object, optional): An object containing the reactive state.
            It must have a 'status_text' attribute that the status label will bind to.

    Returns:
        tuple[ui.element, ui.textarea, ui.label]: Tuple of (chat_container, input_field, status_label)
    """
    logger.info("Creating chat UI using ChatUIBuilder")

    # Create UI builder and build the interface
    ui_builder = ChatUIBuilder(
        on_send=on_send,
        on_new_conversation=on_new_conversation,
        tool_registry=tool_registry,
        core=core,
        form_submit_handler=form_submit_handler,
        status_text_ref=status_text_ref,
        state_manager=state_manager
    )

    return ui_builder.build_ui()
