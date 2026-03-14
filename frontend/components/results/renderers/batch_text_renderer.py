"""
Batch Text Result Renderer

This module provides rendering functions for batch text results.
"""

import logging
from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import for type hints only
    from rb.api.models import BatchTextResponse

from nicegui import ui
from frontend.chatbot.utils import calculate_text_area_height

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

    logger.info("🔍 DEBUG: BatchTextResponse details:")
    logger.info("🔍 DEBUG: Response type: %s", type(response))
    logger.info("🔍 DEBUG: Response dir: %s", [attr for attr in dir(response) if not attr.startswith('_')])
    logger.info("🔍 DEBUG: Has texts attr: %s", hasattr(response, 'texts'))

    if hasattr(response, 'texts'):
        logger.info("🔍 DEBUG: Texts type: %s", type(response.texts))
        logger.info("🔍 DEBUG: Texts length: %s", len(response.texts) if response.texts else 'None')
        if response.texts and len(response.texts) > 0:
            logger.info("🔍 DEBUG: First text_info: %s", response.texts[0])
            logger.info("🔍 DEBUG: First text_info type: %s", type(response.texts[0]))
            logger.info("🔍 DEBUG: First text_info dir: %s", [attr for attr in dir(response.texts[0]) if not attr.startswith('_')])
            if hasattr(response.texts[0], 'value'):
                logger.info("🔍 DEBUG: First text value (first 100 chars): %s", repr(response.texts[0].value[:100]))

    # Validate response structure
    if not hasattr(response, 'texts') or not response.texts:
        logger.warning("BatchTextResponse has no texts or empty texts array")
        with container:
            with ui.card().classes('bg-yellow-50 border-2 border-yellow-300 rounded-lg p-4 m-2'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('warning', size='2rem').classes('text-yellow-600')
                    with ui.column().classes('flex-1'):
                        ui.label('📝 No Transcription Results').classes('text-lg font-bold text-yellow-800')
                        ui.label('The audio processing completed but no transcription text was found.').classes('text-yellow-700')
        return

    logger.info("Rendering batch text result with %d items", len(response.texts))
    texts = response.texts

    try:
        with container:
            # DEBUG: Add a visible test element first
            # ui.label("🔴 VISIBLE TEST: If you see this, container works").classes('text-white bg-red-600 p-4 rounded-lg font-bold text-lg mb-4 border-4 border-black')

            with ui.card().classes('bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow relative'):
                # ui.label("🔵 CARD TEST: If you see this, card works").classes('text-white bg-blue-600 p-4 rounded-lg font-bold mb-4')

                # Content area - test without scroll area
                # Header for test visibility and accessibility
                with ui.row().classes('p-4 items-center'):
                    ui.label('📦 Batch Text Result').classes('text-lg font-bold')

                logger.info("🔍 DEBUG: Creating content without scroll area")
                content_column = ui.column().classes('p-4 gap-3 bg-orange-100 border-4 border-orange-600 rounded-lg')

                try:
                    from frontend.components.results.batch_text_list import render_batch_text_list
                    render_batch_text_list(content_column, texts)
                except Exception as e:
                    logger.exception("Failed to render batch text list component: %s", e)
                    # Fallback to inline per-item rendering
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

        # Display error message in the container
        with container:
            with ui.card().classes('bg-red-50 border-2 border-red-300 rounded-lg p-4 m-2'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('error_outline', size='2rem').classes('text-red-600')
                    with ui.column().classes('flex-1'):
                        ui.label('🚫 UI Rendering Error').classes('text-lg font-bold text-red-800')
                        ui.label('Failed to display transcription results due to a UI rendering error.').classes('text-red-700')
                        ui.label(f'Error: {str(e)}').classes('text-sm text-red-600 mt-2 font-mono')

                # Recovery options
                with ui.row().classes('gap-2 mt-4'):
                    ui.button('Reload Page', icon='refresh', on_click=lambda: ui.navigate.reload()).classes('bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded')
                    ui.button('Go Back', icon='arrow_back', on_click=lambda: ui.navigate.back()).classes('bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded')
