import logging
from nicegui import ui
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_conversation_card(container: ui.column, conversation: Any, view_callback, load_callback) -> None:
    """
    Render a conversation card in the list.

    Args:
        container: Container to add card to
        conversation: ConversationRecord-like object with attributes:
                      conversation_id, title, updated_at, message_count
        view_callback: callable(conversation_id) to view conversation
        load_callback: callable(conversation_id) to load conversation
    """
    try:
        with container:
            with ui.card().classes('p-4 cursor-pointer hover:bg-gray-50'):
                # Title and timestamp
                with ui.row().classes('items-center justify-between mb-2'):
                    ui.label(conversation.title).classes('font-semibold flex-1')
                    # allow caller to format timestamp if needed
                    ts = getattr(conversation, 'updated_at', None)
                    ui.label(str(ts)).classes('text-xs text-gray-500')

                # Message count (includes user queries, assistant responses, tool results, errors)
                msg_count = getattr(conversation, 'message_count', 0)
                if msg_count and int(msg_count) > 0:
                    ui.label(f'{msg_count} messages').classes('text-sm text-gray-600 mb-2')

                # Actions
                with ui.row().classes('gap-2'):
                    ui.button(
                        'View',
                        on_click=lambda cid=getattr(conversation, 'conversation_id', None): view_callback(cid)
                    ).classes('text-sm bg-blue-600 text-white')

                    ui.button(
                        'Load',
                        on_click=lambda cid=getattr(conversation, 'conversation_id', None): load_callback(cid)
                    ).classes('text-sm bg-green-600 text-white')
    except Exception as e:
        logger.exception("Error rendering conversation card: %s", e)
