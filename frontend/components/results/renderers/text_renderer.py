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
from frontend.components.results.text_search_results_view import (
    is_text_search_payload,
    render_text_search_json,
)

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_text(container, response):
    """
    Render text result.

    Displays plain text content with markdown rendering support.
    If the text is image-summary JSON (object with ``image_summary``, ``input_dir``, ``files``),
    shows thumbnails next to each description. Legacy plain JSON arrays of paths still use
    a searchable table without thumbnails.

    Args:
        container: UI container to add preview to
        response (TextResponse): Text response containing value and optional title

    Returns:
        None

    Tips:
    - Text is rendered as markdown for formatting support
    - Image-summary object JSON provides thumbnails + search; legacy file-list JSON is table-only
    - Scrollable container for long text (max height)
    - Title is displayed if provided
    """
    # Lazy import to avoid circular dependencies
    from rb.api.models import TextResponse

    # logger.debug("Rendering text result")
    text = response.value
    title = response.title or 'Text Result'

    # Text search /search JSON → summary + table
    try:
        parsed = json.loads(text)
        if is_text_search_payload(parsed):
            render_text_search_json(container, parsed, title=title)
            # logger.debug("Rendered as text search results table")
            return
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # Image-summary structured JSON (includes input_dir for thumbnails)
    try:
        parsed_paths = json.loads(text)
        if isinstance(parsed_paths, dict) and parsed_paths.get('image_summary'):
            from frontend.components.results.image_summary_results_view import (
                render_image_summary_file_list,
            )
            render_image_summary_file_list(container, parsed_paths, title)
            # logger.debug('Rendered as image summary with thumbnails')
            return
    except (json.JSONDecodeError, ValueError, TypeError, ImportError):
        pass

    # Legacy: JSON array of summary file paths (image-summary output)
    try:
        file_paths = json.loads(text)
        if isinstance(file_paths, list) and all(isinstance(p, str) for p in file_paths):
            try:
                from frontend.components.results.searchable_file_list import render_searchable_file_list
                render_searchable_file_list(container, file_paths, title)
                # logger.debug("Rendered as searchable file list (via component)")
                return
            except Exception:
                pass
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # Use reusable text card component for rendering
    try:
        render_text_card(container, text, title)
        # logger.debug("Text result rendered successfully (via text_card)")
    except Exception as e:
        logger.exception("Failed to render text via text_card: %s", e)
        # Fallback to inline rendering
        with container:
            with ui.card().classes(
                'w-full bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-300 '
                'rounded-xl shadow-lg overflow-hidden'
            ):
                with ui.row().classes('w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white p-4 items-center'):
                    ui.icon('article', size='1.5rem').classes('mr-3')
                    ui.label('📝 Text Result').classes('text-lg font-bold')
                    if title and title != 'Text Result':
                        ui.label(f'• {title}').classes('text-blue-100 ml-2')
                with ui.scroll_area().classes('w-full h-96'):
                    with ui.column().classes('w-full p-6'):
                        ui.markdown(text).classes('prose prose-sm max-w-none text-gray-800 leading-relaxed')


def _render_searchable_file_list(container, file_paths: list, title: str):
    """
    Delegates searchable file list rendering to extracted component.
    """
    from frontend.components.results.searchable_file_list import render_searchable_file_list
    render_searchable_file_list(container, file_paths, title)
