"""
Markdown Result Renderer

This module provides rendering functions for markdown results.
"""

import logging
from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import for type hints only
    from rb.api.models import MarkdownResponse

from nicegui import ui

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_markdown(container, response):
    """
    Render markdown result.

    Displays markdown content with full formatting support.

    Args:
        container: UI container to add preview to
        response: Markdown response containing markdown text

    Returns:
        None

    Tips:
    - Uses prose classes for better markdown styling
    - Full markdown feature support (headings, lists, tables, etc.)
    """
    # Lazy import to avoid circular dependencies
    from rb.api.models import MarkdownResponse

    logger.debug("Rendering markdown result")
    markdown = response.value
    try:
        from frontend.components.results.markdown_card import render_markdown_card
        render_markdown_card(container, markdown)
    except Exception as e:
        logger.exception("Failed rendering markdown card: %s", e)
        with container:
            ui.label(f'Error rendering markdown: {e}').classes('text-red-600')
