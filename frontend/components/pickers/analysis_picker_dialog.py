from nicegui import ui
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def show_analysis_picker_dialog(container: ui.element, options: Dict[int, Dict[str, Any]], on_selected: Callable[[str], Any]):
    """
    Render analysis picker UI inside container.
    """
    with container:
        with ui.card().classes('bg-white p-4 flex-1'):
            ui.label('Choose what you want to analyze:').classes('font-semibold mb-3')
            with ui.column().classes('gap-2'):
                for num, option in options.items():
                    ui.button(
                        f'{num}. {option["name"]} - {option["desc"]}',
                        on_click=lambda n=num: on_selected(option['name'])
                    ).classes('text-left p-2 h-auto whitespace-normal justify-start text-sm bg-slate-100 text-slate-800 border border-slate-200 hover:bg-slate-200')
    return container

