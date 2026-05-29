"""
Table Helper Utilities

This module provides reusable utilities for creating sortable tables
with consistent styling and behavior across result renderers.
"""

import logging
from nicegui import ui
from typing import List, Dict, Callable, Optional

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_sortable_table(
    container,
    columns: List[Dict],
    rows: List[Dict],
    row_key: str = 'id',
    on_row_click: Optional[Callable] = None,
    tip_message: Optional[str] = None,
    show_row_labels: bool = False,
    *,
    table_extra_classes: str = "",
    tip_message_classes: str = "text-xs text-zinc-500 mt-2",
):
    """
    Create a sortable table with consistent styling.
    
    Args:
        container: UI container to add table to (should already be inside a card if needed)
        columns (List[Dict]): List of column definitions with 'name', 'label', 'field', 'align', 'sortable'
        rows (List[Dict]): List of row data dictionaries
        row_key (str): Key to use as unique identifier for rows. Defaults to 'id'.
        on_row_click (Optional[Callable]): Callback function for row click events. Receives event args.
        tip_message (Optional[str]): Optional tip message to display below table
        table_extra_classes: Extra Tailwind classes for the table (e.g. ``text-base``).
        tip_message_classes: Classes for the tip label (default small gray).
        show_row_labels: If True, duplicate each cell as a plain label below the table (for tests only;
            otherwise the table alone shows the data and duplicate blocks look like broken UI).
    
    Returns:
        ui.table: The created table component
    
    Tips:
    - All columns should have 'sortable': True for consistency
    - Row click handler receives event args where e.args[1] is typically the row index
    - Use row_key to match rows in click handlers
    - Container should already be inside appropriate card styling if needed
    """
    logger.debug("Creating sortable table with %d columns and %d rows", len(columns), len(rows))
    
    # Create table with sortable columns (add directly to container)
    with container:
        tc = f"w-full min-w-0 {table_extra_classes}".strip()
        table = ui.table(
            columns=columns,
            rows=rows,
            row_key=row_key,
        ).classes(tc).props('flat bordered')

        # Range-detection and range-sort UI removed — keep table simple and rely on built-in column sorting.

        # Optional: duplicate each cell as labels (e.g. integration tests that don't read table DOM)
        if show_row_labels:
            for r in rows:
                with ui.row().classes('gap-2 mt-1'):
                    for col in columns:
                        field = col.get('field') or col.get('name')
                        # Prefer a full version of the field if available (e.g., 'content_full' for 'content')
                        value = r.get(f"{field}_full", r.get(field, ''))
                        ui.label(str(value)).classes('text-xs text-zinc-600 whitespace-pre-wrap break-words')
        
        # Add click handler if provided
        if on_row_click:
            table.on('rowClick', on_row_click)
        
        # Add tip message if provided
        if tip_message:
            ui.label(f'💡 {tip_message}').classes(tip_message_classes)
    
    logger.debug("Sortable table created successfully")
    return table


def create_metadata_table_columns(
    base_columns: List[Dict],
    metadata_keys: List[str]
) -> List[Dict]:
    """
    Create column definitions including metadata keys.
    
    Args:
        base_columns (List[Dict]): Base column definitions (e.g., Path, Title)
        metadata_keys (List[str]): List of metadata keys to add as columns
    
    Returns:
        List[Dict]: Complete column definitions with metadata columns added
    
    Tips:
    - Metadata keys are converted to lowercase with underscores for field names
    - All columns are set to sortable by default
    - Original key names are preserved as labels
    """
    columns = base_columns.copy()
    
    for key in metadata_keys:
        columns.append({
            'name': key.lower().replace(' ', '_'),
            'label': key,
            'field': key.lower().replace(' ', '_'),
            'align': 'left',
            'sortable': True
        })
    
    logger.debug("Created %d columns (%d base + %d metadata)", len(columns), len(base_columns), len(metadata_keys))
    return columns


def resolve_table_row_index(e, rows: List[Dict]) -> Optional[int]:
    """
    Resolve the clicked row index from a NiceGUI table rowClick event.

    Args:
        e: Event from table.on('rowClick', ...)
        rows: Same list passed to ui.table(rows=...)

    Returns:
        Row index or None if it could not be resolved.
    """
    try:
        candidate = e.args[1] if len(e.args) > 1 else None
        row_index = None

        if isinstance(candidate, int):
            row_index = candidate
        elif isinstance(candidate, dict):
            try:
                row_index = rows.index(candidate)
            except ValueError:
                for key in ('index', 'rowIndex', 'row_idx'):
                    try:
                        maybe = candidate.get(key)
                        if isinstance(maybe, int):
                            row_index = maybe
                            break
                    except Exception:
                        continue
        else:
            try:
                for i, r in enumerate(rows):
                    if candidate == r or candidate == r.get('id') or candidate == r.get('uid'):
                        row_index = i
                        break
            except Exception:
                row_index = None

        if row_index is not None and isinstance(row_index, int) and 0 <= row_index < len(rows):
            return row_index
    except Exception:
        pass
    return None


def create_file_row_click_handler(rows: List[Dict], open_file_func: Callable):
    """
    Create a row click handler that opens files.
    
    Args:
        rows (List[Dict]): List of row data, each should have 'path' or 'path_full' key
        open_file_func (Callable): Function to call with file path (e.g., open_file from results_utils)
    
    Returns:
        Callable: Event handler function
    
    Tips:
        - Rows should have 'path_full' or 'path' key containing the file path
        - Handler expects e.args[1] to be the row index
        - Errors are logged but don't interrupt execution
    """
    def on_row_click(e):
        """Handle row click to open file"""
        try:
            row_index = resolve_table_row_index(e, rows)
            if row_index is not None:
                file_path = rows[row_index].get('path_full') or rows[row_index].get('path')
                if file_path:
                    open_file_func(file_path)
        except Exception as ex:
            logger.warning("Error opening file from table row click: %s", str(ex))
    
    return on_row_click


def create_directory_row_click_handler(rows: List[Dict], open_folder_func: Callable):
    """
    Create a row click handler that opens directories.
    
    Args:
        rows (List[Dict]): List of row data, each should have 'path' or 'path_full' key
        open_folder_func (Callable): Function to call with directory path (e.g., open_folder from results_utils)
    
    Returns:
        Callable: Event handler function
    
    Tips:
    - Rows should have 'path_full' or 'path' key containing the directory path
    - Handler expects e.args[1] to be the row index
    - Errors are logged but don't interrupt execution
    """
    def on_row_click(e):
        """Handle row click to open directory"""
        try:
            row_index = resolve_table_row_index(e, rows)
            if row_index is not None:
                dir_path = rows[row_index].get('path_full') or rows[row_index].get('path')
                if dir_path:
                    open_folder_func(dir_path)
        except Exception as ex:
            logger.warning("Error opening directory from table row click: %s", str(ex))
    
    return on_row_click

