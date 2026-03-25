import logging
from nicegui import ui
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_text_card(container: ui.element, text: str, title: str = "Text Result") -> None:
    """Render plain text content inside a styled card with scroll area."""
    try:
        with container:
            with ui.card().classes(
                'w-full bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-300 '
                'rounded-xl shadow-lg overflow-hidden'
            ):
                # Header (use stable label expected by tests)
                with ui.row().classes('w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white p-4 items-center'):
                    ui.icon('article', size='1.5rem').classes('mr-3')
                    ui.label('📝 Text Result').classes('text-lg font-bold')
                    if title and title != 'Text Result':
                        ui.label(f'• {title}').classes('text-blue-100 ml-2')

                # Content with scroll area
                with ui.scroll_area().classes('w-full h-96'):
                    with ui.column().classes('w-full p-6'):
                        ui.markdown(text).classes('prose prose-sm max-w-none text-gray-800 leading-relaxed')
        logger.debug("Text card rendered successfully")
    except Exception as e:
        logger.exception("Error rendering text card: %s", e)
        with container:
            ui.label(f'Error rendering text: {e}').classes('text-red-600')

