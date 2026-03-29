import logging
from nicegui import ui
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_batch_text_item(container: ui.element, text_info: Any, index: int) -> None:
    """
    Render a single batch text item card inside the given container.
    """
    try:
        full_text = getattr(text_info, 'value', '') or ''
        title = getattr(text_info, 'title', None) or f'Item {index}'

        with container:
            with ui.card().classes('bg-white p-4 rounded-lg border'):
                ui.label(f"📁 INPUT FILE: {title}").classes('text-sm bg-blue-200 p-3 rounded border-2 border-blue-800 font-mono mb-2')
                ui.label(f"📖 TRANSCRIBED TEXT:\n{full_text}").classes('text-sm bg-red-200 p-4 rounded border-2 border-red-800 whitespace-pre-wrap font-mono max-w-full')
    except Exception as e:
        logger.exception("Error rendering batch text item: %s", e)
        with container:
            ui.label(f'Error rendering item: {e}').classes('text-red-600')

