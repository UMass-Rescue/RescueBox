from nicegui import ui
import logging
from typing import Callable, Dict, Any
from frontend.chatbot.config import ToolRegistry

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def show_tool_picker_dialog(container: ui.element, tool_registry: ToolRegistry, on_tool_selected: Callable[[str, Dict[str, Any]], None]):
    """
    Show the tool picker UI inside provided container.
    """
    with container:
        with ui.card().classes('bg-white p-4 flex-1'):
            ui.label('Available Tools').classes('font-semibold')
            ui.label('Click a tool to use').classes('text-sm text-gray-500 mb-3')
            with ui.column().classes('gap-2'):
                for num, tool in tool_registry.TOOL_MENU.items():
                    ui.button(
                        f'{num}. {tool["name"]} - {tool["desc"]}',
                        on_click=lambda n=num, t=tool: on_tool_selected(t['endpoint'], {})
                    ).classes('text-left p-2 h-auto whitespace-normal justify-start text-sm bg-slate-100 text-slate-800 border border-slate-200 hover:bg-slate-200')

    return container

