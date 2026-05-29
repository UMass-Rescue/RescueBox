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
                'rb-job-text-result-card w-full rounded-xl shadow-lg overflow-hidden'
            ):
                with ui.row().classes('rb-job-text-result-header w-full p-4 items-center'):
                    ui.label('Text Result').classes('text-lg font-bold text-zinc-900')
                    if title and title != 'Text Result':
                        ui.label(f'• {title}').classes(
                            'ml-2 opacity-90 text-sm font-medium text-zinc-700'
                        )

                # Content with scroll area
                with ui.scroll_area().classes('w-full h-96'):
                    with ui.column().classes('w-full p-6'):
                        ui.markdown(text).classes(
                            'prose prose-sm max-w-none text-zinc-900 leading-relaxed'
                        )
        logger.debug("Text card rendered successfully")
    except Exception as e:
        logger.exception("Error rendering text card: %s", e)
        with container:
            ui.label(f'Error rendering text: {e}').classes('text-red-600')

