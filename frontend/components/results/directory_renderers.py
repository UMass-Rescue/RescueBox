"""
Directory Result Renderers

This module provides rendering functions for directory-related response types:
- DirectoryResponse: Single directory results
- BatchDirectoryResponse: Multiple directory results
"""

import logging
import os
from nicegui import ui
from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import for type hints only
    from rb.api.models import DirectoryResponse, BatchDirectoryResponse

from frontend.components.results.results_utils import open_file, open_folder
from frontend.components.results.table_helpers import (
    create_sortable_table,
    create_directory_row_click_handler,
)

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_directory(container, response):
    """
    Render directory result.

    Displays directory information with file listing in a sortable table.
    Shows all files with sortable filename column and a button to open the directory.

    Args:
        container: UI container to add preview to
        response: Directory response object containing path
    
    Returns:
        None
    
    Tips:
    - Shows all files in the directory in a sortable table
    - Displays total file count
    - Filename column is sortable
    - File listing errors are silently ignored
    """
    # Lazy import to avoid circular dependencies
    from rb.api.models import DirectoryResponse

    logger.debug("Rendering directory: %s", response.path)
    dir_path = response.path
    title = response.title
    
    # Delegate to reusable directory card for single directory rendering.
    try:
        from frontend.components.results.directory_card import render_directory_card
        render_directory_card(container, response)
        logger.debug("Directory rendered successfully (via directory_card)")
    except Exception as e:
        logger.exception("Falling back to inline directory renderer: %s", e)
        # fallback to original inline behavior if needed
        with container:
            with ui.card().classes('bg-indigo-50 border border-indigo-300 p-4'):
                with ui.column().classes('gap-2'):
                    ui.label('📁 Directory Result').classes('font-bold')
                    ui.label(title).classes('text-sm')
                    ui.label(dir_path).classes('text-xs text-zinc-600 font-mono')
                    ui.button('Open Folder', on_click=lambda: open_folder(dir_path)).classes('rb-brand-primary text-white mt-2')


def render_batch_directory(container, response):
    """
    Render batch directory result.

    Displays multiple directories in a sortable table format.
    Shows all directories with sortable columns for Path, Title, and Subtitle.

    Args:
        container: UI container to add preview to
        response: Batch directory response containing list of directories

    Returns:
        None
    
    Tips:
    - Renders as a sortable datatable using NiceGUI's ui.table
    - All columns (Path, Title, Subtitle) are sortable
    - Clicking a row opens the directory in file explorer
    """
    # Lazy import to avoid circular dependencies
    from rb.api.models import BatchDirectoryResponse

    logger.debug("Rendering batch directory result with %d directories", len(response.directories))
    directories = response.directories
    
    try:
        from frontend.components.results.batch_directory_table import render_batch_directory_table
        render_batch_directory_table(container, directories, open_folder)
        logger.debug("Batch directory result rendered successfully (via component)")
    except Exception as e:
        logger.exception("Falling back to inline batch directory renderer: %s", e)
        with container:
            with ui.card().classes('bg-indigo-50 border border-indigo-300 p-4'):
                with ui.column().classes('gap-2'):
                    ui.label(f'📁 Batch Directory Result ({len(directories)})').classes('font-bold')
                    # fallback inline table
                    with ui.card().classes('bg-white p-4'):
                        on_row_click = create_directory_row_click_handler(
                            [{'path': os.path.basename(getattr(d, 'path', '')), 'path_full': getattr(d, 'path', '')} for d in directories],
                            open_folder
                        )
                        table_column = ui.column()
                        create_sortable_table(
                            table_column,
                            [
                                {'name': 'path', 'label': 'Path', 'field': 'path', 'align': 'left', 'sortable': True},
                                {'name': 'title', 'label': 'Title', 'field': 'title', 'align': 'left', 'sortable': True},
                                {'name': 'subtitle', 'label': 'Subtitle', 'field': 'subtitle', 'align': 'left', 'sortable': True},
                            ],
                            [{'path': os.path.basename(getattr(d, 'path', '')), 'title': getattr(d, 'title', '') or '', 'subtitle': getattr(d, 'subtitle', ''), 'path_full': getattr(d, 'path', '')} for d in directories],
                            row_key='path',
                            on_row_click=on_row_click,
                            tip_message='Tip: Click on any row to open the directory'
                        )
                        for d in directories:
                            try:
                                ui.label(getattr(d, 'title', '') or os.path.basename(getattr(d, 'path', ''))).classes('text-sm')
                            except Exception:
                                ui.label(os.path.basename(getattr(d, 'path', ''))).classes('text-sm')

