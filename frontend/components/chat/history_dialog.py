import asyncio
from typing import Callable

from nicegui import ui

from frontend.components.chat.panels.history_panel import (
    create_history_panel,
    refresh_conversations,
)
from frontend.design_tokens import Design


def show_history_dialog(
    on_conversation_select: Callable[[str], None],
    on_rerun_tool: Callable[[str], None],
) -> ui.dialog:
    """
    Show a modal dialog containing the conversation history panel.

    Args:
        on_conversation_select: callback called with selected conversation_id
        on_rerun_tool: callback called with message id to rerun

    Returns:
        dialog: the NiceGUI dialog element (opened)
    """
    panel_ref: list = [None]

    def _refresh() -> None:
        p = panel_ref[0]
        if p is not None:
            asyncio.create_task(refresh_conversations(p))

    with ui.dialog() as dialog, ui.card().classes(Design.PANEL_SHELL_CARD_NARROW):
        with ui.row().classes(Design.PANEL_SHELL_HEADER):
            ui.label('Chat History').classes(Design.PANEL_SHELL_HEADER_TITLE)
            with ui.row().classes('gap-2 items-center'):
                ui.button('Refresh', icon='refresh', on_click=_refresh).classes(
                    f'{Design.BTN_PRIMARY_TIGHT} !text-sm !py-1 min-h-0'
                )
                ui.button(icon='close', on_click=dialog.close, color=None).props(
                    'flat round dense'
                ).classes(Design.PANEL_SHELL_HEADER_ICON)

        with ui.column().classes(f'{Design.PANEL_SHELL_BODY} flex flex-col min-h-0 max-h-[60vh]'):
            panel_ref[0] = create_history_panel(
                on_conversation_select=lambda conv_id: [
                    on_conversation_select(conv_id),
                    dialog.close(),
                ],
                on_rerun_tool=lambda msg_id: [
                    on_rerun_tool(msg_id),
                    dialog.close(),
                ],
                show_title=False,
            )

    dialog.open()
    return dialog
