"""
Batch Text Result Renderer

This module provides rendering functions for batch text results.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import for type hints only
    from rb.api.models import BatchTextResponse

from nicegui import ui

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_batch_text(container, response):
    """
    Render batch text result with modern expandable cards.

    Displays multiple text items in individual expandable cards with full content
    in scroll readers. No truncation - shows complete text for each item.

    Args:
        container: UI container to add preview to
        response: Batch text response containing list of texts

    Returns:
        None

    Tips:
        - Each text item gets its own expandable card
        - Full text content displayed in scroll readers
        - Modern card design with gradients and shadows
        - Expandable sections to manage space efficiently
    """
    # Lazy import to avoid circular dependencies
    from rb.api.models import BatchTextResponse

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("BatchTextResponse type=%s texts=%s", type(response), getattr(response, "texts", None))

    # Validate response structure
    if not hasattr(response, 'texts') or not response.texts:
        logger.warning("BatchTextResponse has no texts or empty texts array")
        with container:
            with ui.row().classes(
                'w-full items-start gap-3 rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3'
            ):
                
                with ui.column().classes('flex-1 min-w-0 gap-1'):
                    ui.label('No transcription text').classes('text-sm font-semibold text-[#505759]')
                    ui.label(
                        'Processing finished, but there is no text to display for this job.'
                    ).classes('text-sm text-zinc-600')
        return

    logger.info("Rendering batch text result with %d items", len(response.texts))
    texts = response.texts

    try:
        with container:
            # Single surface: header strip + content (no nested loud boxes)
            with ui.column().classes(
                'w-full min-w-0 rounded-xl border border-zinc-200 bg-white overflow-hidden '
                'shadow-sm'
            ):
                with ui.row().classes(
                    'w-full px-4 py-3 items-center gap-2 border-b border-indigo-100 '
                    'bg-gradient-to-r from-indigo-50 to-white'
                ):
                   
                    ui.label('Transcription').classes('text-sm font-semibold text-[#505759]')
                    ui.label(f'{len(texts)} file(s)').classes(
                        'text-xs text-zinc-500 ml-auto tabular-nums'
                    )

                content_column = ui.column().classes('w-full min-w-0 p-4 gap-0')

                try:
                    from frontend.components.results.batch_text_list import render_batch_text_list
                    render_batch_text_list(content_column, texts)
                except Exception as e:
                    logger.exception("Failed to render batch text list component: %s", e)
                    from frontend.components.results.batch_text_item import render_batch_text_item
                    for i, text_info in enumerate(texts, 1):
                        try:
                            render_batch_text_item(content_column, text_info, i)
                        except Exception as ie:
                            logger.exception("Failed to render batch text item %d: %s", i, ie)

        logger.debug("Text result rendered successfully")

    except Exception as e:
        logger.error("Failed to render batch text UI: %s", str(e))
        logger.error("Error type: %s", type(e).__name__)
        import traceback
        logger.error("UI rendering traceback: %s", traceback.format_exc())

        with container:
            with ui.column().classes(
                'w-full gap-3 rounded-xl border border-red-200 bg-red-50/80 px-4 py-3'
            ):
                with ui.row().classes('items-start gap-2'):
                    ui.icon('error_outline', size='1.25rem').classes('text-red-600 shrink-0 mt-0.5')
                    with ui.column().classes('flex-1 min-w-0 gap-1'):
                        ui.label('Could not display transcription').classes(
                            'text-sm font-semibold text-red-900'
                        )
                        ui.label(
                            'Something went wrong while building this view.'
                        ).classes('text-sm text-red-800/90')
                        ui.label(f'{str(e)}').classes(
                            'text-xs text-red-700/90 font-mono mt-1 break-all'
                        )
                with ui.row().classes('gap-2 flex-wrap'):
                    ui.button('Reload Page', icon='refresh', on_click=lambda: ui.navigate.reload()).classes(
                        'rb-brand-primary text-white px-4 py-2 rounded-lg font-medium shadow-sm'
                    )
                    ui.button('Go Back', icon='arrow_back', on_click=lambda: ui.navigate.back()).classes(
                        'border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 '
                        'px-4 py-2 rounded-lg font-medium'
                    )
