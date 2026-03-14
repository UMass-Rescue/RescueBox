"""
File Result Renderers

This module provides rendering functions for file-related response types:
- FileResponse: Single file results
- BatchFileResponse: Multiple file results with metadata support
"""

import logging
import os
from pathlib import Path
import sys
from nicegui import ui
from typing import TYPE_CHECKING
from frontend.components.results.results_utils import open_file
from frontend.components.results.table_helpers import (
    create_sortable_table,
    create_metadata_table_columns,
    create_file_row_click_handler,
)

if TYPE_CHECKING:
    # Import for type hints only
    from rb.api.models import FileResponse, BatchFileResponse




# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_file(container, response):
    """
    Render file result.

    Displays file information with preview for images and action buttons
    for opening the file or its containing folder.

    Args:
        container: UI container to add preview to
        response: File response object containing path and metadata

    Returns:
        None

    Tips:
        - Images are displayed inline using ui.image
        - Other file types show "Open File" and "Open Folder" buttons
        - File path is shown in monospace font for readability
    """
    # Lazy import to avoid circular dependencies
    from rb.api.models import FileResponse

    # Delegate to the reusable file card component to reduce duplication and centralize behavior.
    try:
        from frontend.components.results.file_card import render_file_card
        render_file_card(container, response)
    except Exception as e:
        logger.exception("Error rendering file: %s", e)
        with container:
            ui.label(f'Error displaying file: {str(e)}').classes('text-red-600')


def render_batch_file(container, response):
    """
    Render batch file result.

    Displays multiple files with metadata in a sortable datatable format when metadata is present,
    otherwise falls back to a grid layout. If metadata exists, creates a table with:
    - Sortable columns (all columns can be sorted by clicking the header)
    - Clickable rows (click any row to open the file)
    - Metadata columns with keys as headings
    - Title column if available

    Args:
        container: UI container to add preview to
        response: Batch file response containing list of files

    Returns:
        None

    Tips:
        - If files have metadata, renders as a sortable datatable using NiceGUI's ui.table
        - All columns (Path, Title, and all metadata columns) are sortable by clicking column headers
    - Clicking any row opens the file
    - Falls back to grid layout if no metadata is present
    - Images are displayed as thumbnails in grid view
    """
    # Lazy import to avoid circular dependencies
    from rb.api.models import BatchFileResponse

    logger.debug("Rendering batch file result with %d files", len(response.files))
    files = response.files
    
    # Check if any files have metadata
    has_metadata = any(f.metadata for f in files)
    
    with container:
        with ui.card().classes('bg-blue-50 border border-blue-300 p-4'):
            with ui.column().classes('gap-2'):
                ui.label(f'📦 Batch File Result ({len(files)} files)').classes('font-bold')
                
                if has_metadata:
                    _render_batch_file_with_metadata(container, files)
                else:
                    _render_batch_file_grid(container, files)
    
    logger.debug("Batch file result rendered successfully")


def _render_batch_file_with_metadata(container, files):
    """Render batch files with metadata in a sortable table."""
    # Collect all unique metadata keys across all files
    all_metadata_keys = set()
    for file_info in files:
        if file_info.metadata:
            all_metadata_keys.update(file_info.metadata.keys())
    
    # Sort metadata keys for consistent column order
    metadata_keys = sorted(list(all_metadata_keys))
    logger.debug("Found metadata keys: %s", metadata_keys)
    
    # Create base columns
    base_columns = [
        {'name': 'path', 'label': 'Path', 'field': 'path', 'align': 'left', 'sortable': True},
        {'name': 'title', 'label': 'Title', 'field': 'title', 'align': 'left', 'sortable': True},
    ]
    
    # Create columns with metadata
    columns = create_metadata_table_columns(base_columns, metadata_keys)
    
    # Create row data
    rows = []
    for file_info in files:
        file_path = file_info.path
        row = {
            'path': os.path.basename(file_path),
            'path_full': file_path,  # Store full path for opening
            'title': file_info.title or '',
        }
        # Add metadata values
        for key in metadata_keys:
            field_name = key.lower().replace(' ', '_')
            value = file_info.metadata.get(key, '') if file_info.metadata else ''
            row[field_name] = str(value)
        rows.append(row)
    
    # Create table with click handler
    on_row_click = create_file_row_click_handler(rows, open_file)

    # Use extracted table component
    try:
        from frontend.components.results.batch_file_table import render_batch_file_table
        render_batch_file_table(container, columns, rows, on_row_click, tip_message='Tip: Click on any row to open the file')
    except Exception:
        # Fallback to inline creation if component fails
        with container:
            table_card = ui.card().classes('bg-white p-4')
            with table_card:
                table_column = ui.column()
                create_sortable_table(
                    table_column,
                    columns,
                    rows,
                    row_key='path',
                    show_row_labels=False,
                    on_row_click=on_row_click,
                    tip_message='Tip: Click on any row to open the file'
                )
                # Plain per-row labels removed to avoid duplication below the table


def _render_batch_file_grid(container, files):
    """Render batch files in a grid layout when no metadata is present."""
    logger.debug("No metadata found, using grid layout")
    
    # Group by file type
    file_types = {}
    for file_info in files:
        file_type = file_info.file_type.value if hasattr(file_info.file_type, 'value') else str(file_info.file_type)
        if file_type not in file_types:
            file_types[file_type] = []
        file_types[file_type].append(file_info)
    
    logger.debug("Grouped files into %d types", len(file_types))
    
    # Display by type
    try:
        from frontend.components.results.file_grid import render_file_grid
        render_file_grid(container, file_types, open_file)
    except Exception:
        # Fallback inline rendering
        with container:
            for file_type, type_files in file_types.items():
                with ui.expansion(f'{file_type.upper()} ({len(type_files)})', icon='folder').classes('w-full'):
                    with ui.grid(columns=3).classes('gap-2 mt-2'):
                        for file_info in type_files[:20]:  # Show first 20
                            file_path = file_info.path
                            if file_type in ['img', 'image']:
                                ui.image(file_path).classes('w-full h-32 object-cover cursor-pointer').on('click', lambda e, path=file_path: open_file(path))
                            else:
                                ui.button(
                                    os.path.basename(file_path),
                                    on_click=lambda path=file_path: open_file(path)
                                ).classes('text-xs truncate text-blue-600 hover:underline').props('flat')

