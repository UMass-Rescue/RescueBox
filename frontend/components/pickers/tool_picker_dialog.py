import logging
from typing import Any, Callable, Dict

from nicegui import ui

from frontend.chatbot.config import ToolRegistry
from frontend.design_tokens import Design

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def show_tool_picker_dialog(
    container: ui.element,
    tool_registry: ToolRegistry,
    on_tool_selected: Callable[[str, Dict[str, Any]], None],
):
    """
    Show the tool picker UI inside provided container.
    """
    with container:
        with ui.card().classes(Design.PANEL_SHELL_CARD_MD):
            with ui.row().classes(Design.PANEL_SHELL_HEADER):
                ui.label("Plugins").classes(Design.PANEL_SHELL_HEADER_TITLE)
                

            with ui.column().classes(f"{Design.PANEL_SHELL_BODY} gap-3"):
                ui.label("Choose a plugin to run.").classes("text-sm text-zinc-600")
                for num, tool in tool_registry.TOOL_MENU.items():
                    row = ui.row().classes(
                        f"w-full min-w-0 py-3 px-3 rounded-lg {Design.CHATBOT_PLUGIN_MENU_ROW}"
                    )
                    row.on(
                        'click',
                        lambda *a, t=tool: on_tool_selected(t['endpoint'], {}),
                    )
                    with row:
                        ui.label(f'{num}. {tool["name"]} — {tool["desc"]}').classes(
                            'w-full text-left text-sm leading-snug font-medium text-zinc-900 '
                            'whitespace-normal break-words'
                        )

    return container

