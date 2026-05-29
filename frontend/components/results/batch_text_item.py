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
            with ui.column().classes(
                'w-full min-w-0 gap-2 pb-4 border-b border-zinc-100 last:border-b-0 last:pb-0'
            ):
                ui.label('Source').classes(
                    'text-xs font-medium text-zinc-500 uppercase tracking-wide'
                )
                ui.label(title).classes('text-sm font-semibold text-zinc-900 break-all')
                with ui.scroll_area().classes('w-full max-h-80 rounded-lg bg-zinc-50 ring-1 ring-zinc-200'):
                    ui.label(full_text).classes(
                        'text-sm text-zinc-800 whitespace-pre-wrap leading-relaxed p-3 block'
                    )
    except Exception as e:
        logger.exception("Error rendering batch text item: %s", e)
        with container:
            ui.label(f'Error rendering item: {e}').classes('text-red-600')

