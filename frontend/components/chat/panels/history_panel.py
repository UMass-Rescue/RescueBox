"""
Chat History Panel

This module provides the main chat history panel component.
"""

import logging
import asyncio
from nicegui import ui
from typing import Callable, Optional
from datetime import datetime

from frontend.database import get_chat_history_db, ConversationRecord, ChatMessageRecord
from frontend.constants import UI_BUTTONS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_history_panel(
    on_conversation_select: Optional[Callable[[str], None]] = None,
    on_rerun_tool: Optional[Callable[[str], None]] = None
) -> ui.column:
    """
    Create a chat history panel component.

    Displays a list of previous conversations with search functionality,
    conversation preview, and re-run buttons for tool calls.

    Args:
        on_conversation_select: Callback when conversation is selected (conversation_id)
        on_rerun_tool: Callback when re-run button is clicked (message_id)

    Returns:
        ui.column: History panel container

    Usage:
        history_panel = create_history_panel(
            on_conversation_select=lambda conv_id: load_conversation(conv_id),
            on_rerun_tool=lambda msg_id: rerun_tool_call(msg_id)
        )
    """
    logger.info("Creating chat history panel")

    panel = ui.column().classes('w-full h-full')

    with panel:
        # Header
        with ui.row().classes('items-center justify-between mb-4'):
            ui.label('Chat History').classes('text-xl font-bold')
            ui.button('Refresh', on_click=lambda: refresh_conversations(panel)).classes('text-sm')

        # Search box
        search_input = ui.input(
            placeholder='Search conversations...',
            on_change=lambda e: filter_conversations(panel, e.value)
        ).classes('w-full mb-4')

        # Conversations list
        conversations_container = ui.column().classes('space-y-2 overflow-y-auto')

    # Load conversations (schedule async refresh)
    try:
        asyncio.create_task(refresh_conversations(panel))
    except Exception:
        # Fallback: call without scheduling (may be running in sync test env)
        try:
            refresh_conversations(panel)
        except Exception:
            logger.debug("Could not schedule refresh_conversations")

    logger.info("Chat history panel created")
    return panel


async def refresh_conversations(container: ui.column):
    """
    Refresh and display conversations list.

    Args:
        container: Container to display conversations in
    """
    logger.info("Refreshing conversations list")

    # Find conversations container (second child after header/search)
    conversations_container = None
    for child in container:
        if hasattr(child, 'classes') and 'space-y-2' in child.classes:
            conversations_container = child
            break

    if not conversations_container:
        logger.warning("Conversations container not found")
        return

    conversations_container.clear()

    try:
        logger.info("Getting chat history database instance")
        chat_history = get_chat_history_db()
        logger.info("Got chat history database, calling get_all_conversations")
        conversations = await chat_history.get_all_conversations()
        logger.info("get_all_conversations returned: %s", conversations)

        if not conversations:
            with conversations_container:
                ui.label('No conversations yet').classes('text-gray-500 text-center py-8')
            logger.info("No conversations found - displaying empty message")
            return

        logger.info("Displaying %d conversations", len(conversations))

        for conv in conversations:
            try:
                # Skip conversations with zero messages
                try:
                    msg_count = int(getattr(conv, 'message_count', 0))
                except Exception:
                    msg_count = 0
                if msg_count == 0:
                    logger.debug("Skipping conversation %s with zero messages", getattr(conv, 'conversation_id', '<unknown>'))
                    continue

                from frontend.components.chat.conversation_card import render_conversation_card as _render_conv
                # supply callbacks from conversation_actions module
                from .conversation_actions import view_conversation, load_conversation
                _render_conv(conversations_container, conv, view_conversation, load_conversation)
            except Exception:
                # fallback to inline rendering if component fails
                try:
                    render_conversation_card(conversations_container, conv)
                except Exception as e:
                    logger.error("Error rendering conversation %s: %s", getattr(conv, 'conversation_id', '<unknown>'), e)
    except Exception as e:
        logger.error("Error refreshing conversations: %s", e)
        with conversations_container:
            ui.label(f'Error loading conversations: {e}').classes('text-red-600')


def render_conversation_card(container: ui.column, conversation: ConversationRecord):
    """
    Render a conversation card in the list.

    Args:
        container: Container to add card to
        conversation: ConversationRecord to display
    """
    from .conversation_utils import _format_timestamp
    from .conversation_actions import view_conversation, load_conversation

    logger.debug("Rendering conversation card: %s", conversation.conversation_id)

    try:
        from frontend.components.chat.conversation_card import render_conversation_card as _render_conv
        from .conversation_actions import view_conversation, load_conversation
        _render_conv(container, conversation, view_conversation, load_conversation)
    except Exception:
        # fallback to inline rendering if component fails
        with container:
            with ui.card().classes('p-4 cursor-pointer hover:bg-gray-50'):
                # Title and timestamp
                with ui.row().classes('items-center justify-between mb-2'):
                    ui.label(conversation.title).classes('font-semibold flex-1')
                    ui.label(_format_timestamp(conversation.updated_at)).classes('text-xs text-gray-500')

                # Message count (includes user queries, assistant responses, tool results, errors)
                try:
                    msg_count = int(getattr(conversation, 'message_count', 0))
                except Exception:
                    msg_count = 0
                if msg_count > 0:
                    ui.label(f'{msg_count} messages').classes('text-sm text-gray-600 mb-2')

                # Actions
                with ui.row().classes('gap-2'):
                    ui.button(
                        'View',
                        on_click=lambda cid=conversation.conversation_id: view_conversation(cid)
                    ).classes('text-sm bg-blue-600 text-white')

                    ui.button(
                        'Load',
                        on_click=lambda cid=conversation.conversation_id: load_conversation(cid)
                    ).classes('text-sm bg-green-600 text-white')


def filter_conversations(container: ui.column, search_term: str):
    """
    Filter conversations by search term.

    Args:
        container: History panel container
        search_term: Search term to filter by
    """
    logger.debug("Filtering conversations: %s", search_term)
    # Implementation: filter displayed conversations
    # For now, just refresh (full implementation would filter in memory)
    if not search_term:
        refresh_conversations(container)
