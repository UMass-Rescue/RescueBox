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

    logger.info("Rendering batch text result with %d items", len(response.texts) if hasattr(response, 'texts') and response.texts else 0)
    texts = response.texts if hasattr(response, 'texts') else []

    with container:
        # DEBUG: Add a visible test element first
        # ui.label("🔴 VISIBLE TEST: If you see this, container works").classes('text-white bg-red-600 p-4 rounded-lg font-bold text-lg mb-4 border-4 border-black')

        with ui.card().classes('bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow relative'):
            # ui.label("🔵 CARD TEST: If you see this, card works").classes('text-white bg-blue-600 p-4 rounded-lg font-bold mb-4')

            # Content area - test without scroll area
            logger.info("🔍 DEBUG: Creating content without scroll area")
            content_column = ui.column().classes('p-4 gap-3 bg-orange-100 border-4 border-orange-600 rounded-lg')

            with content_column:
                logger.info("🔍 DEBUG: Inside column context, texts length: %d", len(texts))
                for i, text_info in enumerate(texts, 1):
                    logger.info("🔍 DEBUG: Processing text item %d: %s", i, type(text_info))

                    # Individual text item card
                    full_text = text_info.value if hasattr(text_info, 'value') else "NO VALUE"
                    logger.info("🔍 DEBUG: Full text length: %d", len(full_text))

                    # DEBUG: Show text directly with HIGH visibility
                    # logger.info("🔍 DEBUG: Creating green label")
                    # green_label = ui.label(f"🟢 ITEM {i} DEBUG: VISIBLE TEXT SHOULD BE HERE")
                    # green_label.classes('font-bold text-green-600 bg-green-200 p-4 rounded-lg border-4 border-green-800 text-xl mb-4')
                    # logger.info("🔍 DEBUG: Created green label: %s", green_label)

                    logger.info("🔍 DEBUG: Creating title label")
                    title_label = ui.label(f"📁 INPUT FILE: {text_info.title if hasattr(text_info, 'title') and text_info.title else 'No title'}")
                    title_label.classes('text-sm bg-blue-200 p-3 rounded border-2 border-blue-800 font-mono mb-2')
                    logger.info("🔍 DEBUG: Created title label: %s", title_label)

                    logger.info("🔍 DEBUG: Creating preview label")
                    preview_label = ui.label(f"📄 PREVIEW: {full_text[:100]}...")
                    preview_label.classes('text-sm bg-yellow-200 p-3 rounded border-2 border-yellow-800 mb-3 font-mono')
                    logger.info("🔍 DEBUG: Created preview label: %s", preview_label)

                    logger.info("🔍 DEBUG: Creating length label")
                    length_label = ui.label(f"📊 LENGTH: {len(full_text)} characters")
                    length_label.classes('text-sm bg-purple-200 p-3 rounded border-2 border-purple-800 font-mono mb-4')
                    logger.info("🔍 DEBUG: Created length label: %s", length_label)

                    logger.info("🔍 DEBUG: Creating full text label")
                    full_text_label = ui.label(f"📖 TRANSCRIBED TEXT:\n{full_text}")
                    full_text_label.classes('text-sm bg-red-200 p-4 rounded border-2 border-red-800 whitespace-pre-wrap font-mono max-w-full')
                    logger.info("🔍 DEBUG: Created full text label: %s", full_text_label)

    logger.debug("Text result rendered successfully")
