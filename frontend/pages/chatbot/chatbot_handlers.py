"""
Chatbot Message Handlers

This module provides handler functions for processing user messages and
routing them to appropriate actions (forms, tool picker, help, etc.).
"""

import logging
from typing import Dict, Any, Callable, Optional
from nicegui import ui
from frontend.chatbot.config import ToolRegistry
from frontend.chatbot.core import ChatbotCore
from frontend.database import JobStatus
from frontend.pages.chatbot.utils import MessageSender, ResultRouter, FormProcessor

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize utility classes
_message_sender = MessageSender()
_result_router = ResultRouter()
_form_processor = FormProcessor()


async def handle_send_message(
    message_text: str,
    input_field: ui.textarea,
    is_processing_ref: dict,
    message_handler,
    process_handler_result_func,
    add_message_func,
    show_error_func,
    update_status_func,
    conversation_id_ref: Optional[dict] = None  # Dict with 'value' key for conversation_id
):
    """
    Handle sending a user message.

    Processes the message text, adds it to chat, handles via message handler,
    and displays the result. Also saves messages to chat history.

    Args:
        message_text: The message text from input field
        input_field: The input field widget
        is_processing_ref: Dict with 'value' key for processing flag
        message_handler: MessageHandler instance
        process_handler_result_func: Function to process handler results
        add_message_func: Function to add messages to chat
        show_error_func: Function to show errors
        update_status_func: Function to update status
        conversation_id_ref: Optional dict with 'value' key for conversation_id

    Returns:
        None
    """
    await _message_sender.send_message(
        message_text=message_text,
        input_field=input_field,
        is_processing_ref=is_processing_ref,
        message_handler=message_handler,
        process_handler_result_func=process_handler_result_func,
        add_message_func=add_message_func,
        show_error_func=show_error_func,
        update_status_func=update_status_func,
        conversation_id_ref=conversation_id_ref
    )


async def process_handler_result(
    result: Dict,
    chat_container: ui.element,
    tool_registry: ToolRegistry,
    add_assistant_message_func,
    show_error_func,
    load_and_show_form_func
):
    """
    Process result from message handler and route to appropriate action.

    Routes the handler result to the appropriate UI action based on result type.

    Args:
        result: Result dictionary from message handler with 'type' key
        chat_container: Container for chat messages
        tool_registry: ToolRegistry instance
        add_assistant_message_func: Function to add assistant messages
        show_error_func: Function to show errors
        load_and_show_form_func: Function to load and show forms

    Returns:
        None

    Result Types:
    - 'help': Display help text
    - 'tool_picker': Show tool picker menu
    - 'show_form': Load and display form for tool
    - 'message': Display assistant message
    - 'error': Display error message
    """
    await _result_router.route_result(
        result=result,
        chat_container=chat_container,
        tool_registry=tool_registry,
        add_assistant_message_func=add_assistant_message_func,
        show_error_func=show_error_func,
        load_and_show_form_func=load_and_show_form_func
    )


async def handle_form_submit(
    request_body,
    endpoint: str,
    task_schema,
    core: ChatbotCore,
    current_form_ref: dict,
    chat_container: ui.element,
    show_results_func,
    show_error_func,
    conversation_id_ref: Optional[dict] = None,  # Dict with 'value' key for conversation_id
    remaining_calls: Optional[list] = None,  # Remaining tool calls for multi-call sequence
    load_and_show_form_func: Optional[Callable] = None  # Function to load next form
):
    """
    Handle form submission by delegating to FormProcessor.

    This function serves as a thin wrapper around FormProcessor.process_form()
    to maintain backward compatibility while eliminating code duplication.

    Args:
        request_body: RequestBody Pydantic model from form
        endpoint: API endpoint for job submission
        task_schema: TaskSchema for the endpoint
        core: ChatbotCore instance
        current_form_ref: Dict with 'value' key for current form widget
        chat_container: Container for chat messages
        show_results_func: Function to show results
        show_error_func: Function to show errors
        conversation_id_ref: Optional dict with 'value' key for conversation_id
        remaining_calls: Remaining tool calls for multi-call sequence
        load_and_show_form_func: Function to load next form

    Returns:
        None
    """
    await _form_processor.process_form(
        request_body=request_body,
        endpoint=endpoint,
        task_schema=task_schema,
        core=core,
        current_form_ref=current_form_ref,
        chat_container=chat_container,
        show_results_func=show_results_func,
        show_error_func=show_error_func,
        conversation_id_ref=conversation_id_ref,
        remaining_calls=remaining_calls,
        load_and_show_form_func=load_and_show_form_func
    )
