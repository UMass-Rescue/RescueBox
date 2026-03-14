from nicegui import ui
import logging
from typing import Callable
from frontend.components.chat import create_history_panel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def show_history_dialog(on_conversation_select: Callable[[str], None], on_rerun_tool: Callable[[str], None]) -> ui.dialog:
    """
    Show a modal dialog containing the conversation history panel.

    Args:
        on_conversation_select: callback called with selected conversation_id
        on_rerun_tool: callback called with message id to rerun

    Returns:
        dialog: the NiceGUI dialog element (opened)
    """
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl max-h-[80vh]'):
        ui.label('Chat History').classes('text-2xl font-bold mb-4')
        create_history_panel(
            on_conversation_select=lambda conv_id: [on_conversation_select(conv_id), dialog.close()],
            on_rerun_tool=lambda msg_id: [on_rerun_tool(msg_id), dialog.close()]
        )
    dialog.open()
    return dialog

