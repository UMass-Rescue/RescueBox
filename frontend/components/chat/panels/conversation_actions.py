"""
Conversation Actions

This module provides functions for performing actions on conversations.
"""

import logging
from nicegui import ui

from frontend.database import get_chat_history_db
from frontend.design_tokens import Design

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def view_conversation(conversation_id: str):
    """
    View full conversation in a dialog.

    Args:
        conversation_id: Conversation unique identifier
    """
    from .conversation_renderer import render_message_in_dialog

    logger.info("Viewing conversation: %s", conversation_id)

    chat_history = get_chat_history_db()
    conversation = await chat_history.get_conversation(conversation_id)
    messages = await chat_history.get_messages(conversation_id)

    if not conversation:
        ui.notify('Conversation not found', type='negative', classes='rb-notify-505759')
        return

    try:
        from frontend.components.chat.conversation_view_dialog import show_conversation_view_dialog
        show_conversation_view_dialog(conversation, messages, title=conversation.title if hasattr(conversation, 'title') else None)
    except Exception:
        # Fallback to inline dialog if component fails
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl max-h-[80vh]'):
            ui.label(f'Conversation: {conversation.title}').classes('text-2xl font-bold mb-4')

            with ui.column().classes('space-y-4 overflow-y-auto'):
                for msg in messages:
                    render_message_in_dialog(msg)

            with ui.row().classes('mt-4'):
                ui.button('Close', on_click=dialog.close).classes(Design.BTN_MEDIUM_GRAY)
                ui.button('Load in Chat', on_click=lambda: [load_conversation(conversation_id), dialog.close()]).classes('rb-brand-primary text-white')

        dialog.open()


async def load_conversation(conversation_id: str):
    """
    Load a conversation into the current chat.

    Uses URL parameter (load_conversation=id) so the page load triggers a full reload
    and the conversation is loaded. Storage-based approach fails when already on
    /chatbot because ui.navigate.to('/chatbot') does not reload the page.

    Args:
        conversation_id: Conversation unique identifier
    """
    logger.info("Loading conversation: %s (using URL param approach)", conversation_id)

    try:
        # Navigate with URL param so page load reads it and loads the conversation.
        # This works even when already on /chatbot (forces reload with param).
        target = f'/chatbot?load_conversation={conversation_id}'
        logger.info("Navigating to %s to load conversation (full reload with param)", target)
        ui.navigate.to(target)
        logger.info("load_conversation: navigation triggered for %s", conversation_id)
    except RuntimeError as ui_error:
        if "slot cannot be determined" in str(ui_error):
            logger.debug("UI navigation skipped in test environment: %s", ui_error)
        else:
            raise
    except Exception as e:
        logger.error("Error loading conversation: %s", e)
        try:
            ui.notify(f'Error loading conversation: {e}', type='negative', classes='rb-notify-505759')
        except RuntimeError as ui_error:
            if "slot cannot be determined" in str(ui_error):
                logger.debug("UI notification skipped in test environment: %s", ui_error)
            else:
                raise


async def rerun_tool_call(message_id: str):
    """
    Rerun a tool call by navigating to chatbot with rerun parameter.

    Args:
        message_id: Message ID of the tool call to rerun
    """
    logger.info("Rerunning tool call: %s", message_id)

    try:
        from frontend.database import get_chat_history_db

        chat_history = get_chat_history_db()
        message = await chat_history.get_tool_call_by_id(message_id)

        if not message:
            ui.notify('Tool call not found for rerun', type='negative', classes='rb-notify-505759')
            return

        if not message.tool_call_endpoint:
            ui.notify('Invalid tool call data for rerun', type='negative', classes='rb-notify-505759')
            return

        # Show what we're rerunning
        ui.notify(f'Re-running: {message.tool_call_endpoint}', type='info', classes='rb-notify-505759')

        # Navigate to chatbot with rerun parameter
        ui.navigate.to(f'/chatbot?rerun={message_id}')

    except Exception as e:
        logger.error("Error rerunning tool call: %s", str(e))
        ui.notify(f'Error rerunning tool call: {e}', type='negative', classes='rb-notify-505759')
