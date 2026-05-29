"""
Conversation Renderer

This module provides functions for rendering conversations and messages.
"""

import logging
from nicegui import ui
from typing import List

from frontend.database import ChatMessageRecord

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_message_in_dialog(message: ChatMessageRecord):
    """
    Render a message in the conversation dialog.

    Args:
        message: ChatMessageRecord to render
    """
    logger.debug("Rendering message in dialog: %s", getattr(message, 'message_id', '<unknown>'))
    try:
        # Prefer extracted message card component
        from frontend.components.chat.message_card import render_message_card as _render_card
        _render_card(ui.column(), message.role, message.content, getattr(message, 'timestamp', None))
        return
    except Exception:
        logger.debug("Falling back to inline conversation message renderer")

    # Inline fallback rendering
    # Determine message type styling
    if message.role == "user":
        bg_color = "bg-indigo-50"
        ring_or_border = "border border-indigo-200"
        text_color = "text-indigo-900"
        align = "justify-start"
        sender = "You"
    elif message.role == "assistant":
        bg_color = "bg-white"
        ring_or_border = "ring-1 ring-zinc-200"
        text_color = "text-zinc-800"
        align = "justify-end"
        sender = "Assistant"
    else:
        bg_color = "bg-zinc-50"
        ring_or_border = "border border-zinc-200"
        text_color = "text-zinc-900"
        align = "justify-center"
        sender = message.role.title()

    with ui.row().classes(f'w-full {align} mb-2'):
        with ui.column().classes(f'max-w-[80%] {align}'):
            # Message header
            with ui.row().classes('items-center gap-2 mb-1'):
                ui.label(sender).classes("text-xs font-semibold text-zinc-600")
                if hasattr(message, "timestamp") and message.timestamp:
                    from .conversation_utils import _format_timestamp
                    ui.label(_format_timestamp(message.timestamp)).classes(
                        "text-xs text-zinc-500"
                    )

            # Message content
            with ui.card().classes(f"{bg_color} {ring_or_border} p-3 rounded-lg"):
                if getattr(message, 'message_type', 'text') == 'text':
                    ui.markdown(getattr(message, 'content', '')).classes(f'prose prose-sm max-w-none {text_color}')
                elif getattr(message, 'message_type', '') == 'tool_call':
                    # Special handling for tool calls
                    ui.label('Tool call').classes('font-semibold text-indigo-900 mb-2')
                    ui.code(getattr(message, 'content', ''), language='json').classes('text-xs')
                elif getattr(message, 'message_type', '') == 'tool_result':
                    # Special handling for tool results
                    ui.label('Tool result').classes('font-semibold text-black mb-2')
                    ui.code(getattr(message, 'content', ''), language='json').classes('text-xs')
                elif getattr(message, 'message_type', '') == 'error':
                    # Special handling for errors
                    ui.label('Error').classes('font-semibold mb-2 text-red-700')
                    ui.label(getattr(message, 'content', '')).classes('text-red-700')
                else:
                    ui.label(getattr(message, 'content', '')).classes(text_color)

                # Show tool calls if present
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    with ui.expansion('Tool Calls', icon='build').classes('mt-2'):
                        for tool_call in message.tool_calls:
                            with ui.card().classes('bg-white border p-2 mt-1'):
                                ui.label(f"Tool: {tool_call.get('name', 'Unknown')}").classes('font-semibold text-sm')
                                if 'arguments' in tool_call:
                                    ui.code(str(tool_call['arguments']), language='json').classes('text-xs mt-1')
