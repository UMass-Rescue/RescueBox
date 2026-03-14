import logging
from nicegui import ui
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_markdown_card(container: ui.element, markdown: str) -> None:
    """Render markdown content inside a styled card."""
    try:
        with container:
            with ui.card().classes('bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-300 rounded-xl shadow-lg overflow-hidden'):
                # Header
                with ui.row().classes('bg-gradient-to-r from-purple-500 to-pink-600 text-white p-4 items-center'):
                    ui.icon('description', size='1.5rem').classes('mr-3')
                    ui.label('📄 Markdown Result').classes('text-lg font-bold')

                # Content with scroll area
                with ui.scroll_area().classes('h-96'):
                    with ui.column().classes('p-6'):
                        ui.markdown(markdown).classes('prose prose-sm max-w-none text-gray-800 leading-relaxed')
        logger.debug("Markdown card rendered successfully")
    except Exception as e:
        logger.exception("Error rendering markdown card: %s", e)
        with container:
            ui.label(f'Error rendering markdown: {e}').classes('text-red-600')

