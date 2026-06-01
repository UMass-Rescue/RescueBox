import logging
from typing import Any, Callable, Dict
from nicegui import ui
from frontend.design_tokens import Design
from frontend.chatbot.config import ToolRegistry

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def show_analysis_picker_dialog(
    container: ui.element,
    options: Dict[int, Dict[str, Any]],
    on_selected: Callable[[str], Any],
):
    """
    Render analysis picker UI inside container.
    """
    with container:
        with ui.card().classes(Design.PANEL_SHELL_CARD_MD):
            with ui.row().classes(Design.PANEL_SHELL_HEADER):
                ui.label("Analysis").classes(Design.PANEL_SHELL_HEADER_TITLE)

            with ui.column().classes(f"{Design.PANEL_SHELL_BODY} gap-2"):
                ui.label("Choose what you want to analyze:").classes(
                    "font-semibold text-zinc-800 -mt-1"
                )
                for num, option in options.items():
                    ui.button(
                        f'{num}. {option["name"]} - {option["desc"]}',
                        on_click=lambda *a, opt=option: on_selected(opt["name"]),
                    ).classes(
                        "text-left p-2 h-auto whitespace-normal justify-start text-sm "
                        "bg-zinc-100 text-zinc-800 border border-zinc-200 hover:bg-zinc-200 w-full"
                    )
    return container


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
                        "click",
                        lambda *a, t=tool: on_tool_selected(t["endpoint"], {}),
                    )
                    with row:
                        ui.label(f'{num}. {tool["name"]} — {tool["desc"]}').classes(
                            "w-full text-left text-sm leading-snug font-medium text-zinc-900 "
                            "whitespace-normal break-words"
                        )

    return container
