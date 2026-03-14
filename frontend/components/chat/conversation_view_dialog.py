import logging
from nicegui import ui
from typing import List, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def show_conversation_view_dialog(conversation: Any, messages: List[Any], title: str = None):
    """
    Show a dialog rendering a conversation and its messages using the
    existing conversation renderer helper.
    """
    try:
        from frontend.components.chat.panels.conversation_renderer import render_message_in_dialog

        with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl max-h-[80vh]'):
            ui.label(f'Conversation: {conversation.title if hasattr(conversation, "title") else title}').classes('text-2xl font-bold mb-4')

            with ui.column().classes('space-y-4 overflow-y-auto'):
                for msg in messages:
                    render_message_in_dialog(msg)

            with ui.row().classes('mt-4'):
                ui.button('Close', on_click=dialog.close).classes('bg-gray-600 text-white')
                # ui.button('Load in Chat', on_click=lambda cid=getattr(conversation, 'conversation_id', None): [ui.run_javascript("console.log('load')"), dialog.close()]).classes('bg-blue-600 text-white')

        dialog.open()
        return dialog
    except Exception as e:
        logger.exception("Failed to show conversation view dialog: %s", e)
        # Fallback: show simple notification
        ui.notify('Unable to show conversation dialog', type='negative')
        return None

