import logging
from nicegui import ui
from typing import Any, List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_batch_text_list(container: ui.element, texts: List[Any]) -> None:
    """
    Render a sequence of batch text items using the extracted item component.
    """
    try:
        from frontend.components.results.batch_text_item import render_batch_text_item

        for i, text_info in enumerate(texts, 1):
            try:
                render_batch_text_item(container, text_info, i)
            except Exception as e:
                logger.exception("Failed rendering batch text item %d: %s", i, e)
                with container:
                    ui.label(f'Error rendering item {i}: {e}').classes('text-red-600')
    except Exception as e:
        logger.exception("Failed to use batch_text_item component: %s", e)
        # Fallback inline: render simple labels
        for i, text_info in enumerate(texts, 1):
            try:
                text_val = getattr(text_info, 'value', text_info.get('value') if isinstance(text_info, dict) else str(text_info))
                with container:
                    with ui.expansion(f'Item {i}').classes('w-full'):
                        ui.label(text_val).classes('text-sm whitespace-pre-wrap')
            except Exception:
                with container:
                    ui.label(f'Item {i}').classes('text-sm')

