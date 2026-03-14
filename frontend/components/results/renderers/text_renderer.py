"""
Text Result Renderer

This module provides rendering functions for plain text results.
"""

import logging
import os
import json
from nicegui import ui
from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import for type hints only
    from rb.api.models import TextResponse

from frontend.components.results.results_utils import open_file
from frontend.components.results.table_helpers import create_sortable_table
from frontend.components.results.text_card import render_text_card

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_text(container, response):
    """
    Render text result.

    Displays plain text content with markdown rendering support.
    If the text is a JSON array of file paths (like image-summary output),
    displays a searchable table where users can search through file contents.

    Args:
        container: UI container to add preview to
        response (TextResponse): Text response containing value and optional title

    Returns:
        None

    Tips:
    - Text is rendered as markdown for formatting support
    - If text is JSON array of file paths, provides searchable table interface
    - Scrollable container for long text (max height)
    - Title is displayed if provided
    """
    # Lazy import to avoid circular dependencies
    from rb.api.models import TextResponse

    logger.debug("Rendering text result")
    text = response.value
    title = response.title or 'Text Result'

    # Check if text is a JSON array of file paths (image-summary output)
    try:
        file_paths = json.loads(text)
        if isinstance(file_paths, list) and all(isinstance(p, str) for p in file_paths):
            # This looks like image-summary output - render with search component
            try:
                from frontend.components.results.searchable_file_list import render_searchable_file_list
                render_searchable_file_list(container, file_paths, title)
                logger.debug("Rendered as searchable file list (via component)")
                return
            except Exception:
                # Fallback to internal handler if component fails
                pass
    except (json.JSONDecodeError, ValueError, TypeError):
        # Not JSON or not a list of strings, render as regular text
        pass

    # Use reusable text card component for rendering
    try:
        render_text_card(container, text, title)
        logger.debug("Text result rendered successfully (via text_card)")
    except Exception as e:
        logger.exception("Failed to render text via text_card: %s", e)
        # Fallback to inline rendering
        with container:
            with ui.card().classes('bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-xl shadow-lg overflow-hidden'):
                with ui.row().classes('bg-gradient-to-r from-blue-500 to-indigo-600 text-white p-4 items-center'):
                    ui.icon('article', size='1.5rem').classes('mr-3')
                    ui.label('📝 Text Result').classes('text-lg font-bold')
                    if title and title != 'Text Result':
                        ui.label(f'• {title}').classes('text-blue-100 ml-2')
                with ui.scroll_area().classes('h-96'):
                    with ui.column().classes('p-6'):
                        ui.markdown(text).classes('prose prose-sm max-w-none text-gray-800 leading-relaxed')


def _render_searchable_file_list(container, file_paths: list, title: str):
    """
    Delegates searchable file list rendering to extracted component.
    """
    from frontend.components.results.searchable_file_list import render_searchable_file_list
    render_searchable_file_list(container, file_paths, title)
