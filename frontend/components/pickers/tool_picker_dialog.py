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
        with ui.card().classes(
            'w-full max-w-md min-w-0 mx-auto p-4 rounded-xl border-2 border-violet-200 '
            'bg-gradient-to-br from-violet-50 via-indigo-50 to-slate-100 shadow-sm'
        ):
            ui.label('Click on a plugin to use').classes('text-sm text-slate-600 mb-2')
            with ui.column().classes('gap-1.5 w-full'):
                for num, tool in tool_registry.TOOL_MENU.items():
                    row = ui.row().classes(
                        'w-full min-w-0 py-3 px-3 rounded-lg border-2 border-violet-200/90 '
                        'bg-white shadow-sm hover:bg-violet-50 hover:border-violet-400 '
                        'cursor-pointer transition-colors duration-150 items-start'
                    )
                    row.on(
                        'click',
                        lambda *a, t=tool: on_tool_selected(t['endpoint'], {}),
                    )
                    with row:
                        ui.label(f'{num}. {tool["name"]} — {tool["desc"]}').classes(
                            'w-full text-left text-sm leading-snug font-medium text-slate-900 '
                            'whitespace-normal break-words'
                        )

    return container

