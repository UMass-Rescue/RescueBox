import logging
import os
from pathlib import Path
from typing import Any, List, Dict
from nicegui import ui

from frontend.components.results.table_helpers import create_sortable_table, create_file_row_click_handler
from frontend.components.results.results_utils import open_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_searchable_file_list(container: ui.element, file_paths: List[str], title: str) -> None:
    """
    Render a searchable list of files with their contents.

    This is used for image-summary output where each file contains text descriptions.
    Users can search through the file contents to find matching files.
    """
    logger.debug("Rendering searchable file list with %d files", len(file_paths))

    # Read file contents
    file_data = []
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                content = Path(file_path).read_text(encoding='utf-8')
                file_data.append({
                    'path': file_path,
                    'filename': os.path.basename(file_path),
                    'content': content,
                    'content_lower': content.lower()  # For case-insensitive search
                })
            else:
                logger.warning("File does not exist: %s", file_path)
        except Exception as e:
            logger.warning("Error reading file %s: %s", file_path, str(e))

    if not file_data:
        with container:
            ui.label('No valid files found').classes('text-red-600')
        return

    with container:
        with ui.card().classes('bg-green-50 border border-green-300 p-4'):
            with ui.column().classes('gap-2'):
                ui.label(f'📝 {title} ({len(file_data)} files)').classes('font-bold')

                # Search input
                search_input = ui.input(
                    label='Search',
                    placeholder='Enter search term (e.g., "blue car")',
                    value=''
                ).classes('w-full').props('clearable')

                # Container for table that will be refreshed
                table_container = ui.column().classes('w-full')
                result_count_label = ui.label(f'Showing {len(file_data)} of {len(file_data)} files').classes('text-xs text-zinc-600')

                def update_table(search_term: str = ''):
                    """Update the table based on search term"""
                    search_lower = search_term.lower().strip()

                    # Filter files where content contains the search term
                    if search_lower:
                        filtered = [
                            f for f in file_data
                            if search_lower in f['content_lower']
                        ]
                    else:
                        filtered = file_data.copy()

                    logger.debug("Filtered to %d files matching '%s'", len(filtered), search_term)

                    # Clear and rebuild table
                    table_container.clear()

                    with table_container:
                        # Prepare columns for sortable table
                        columns = [
                            {'name': 'filename', 'label': 'Filename', 'field': 'filename', 'align': 'left', 'sortable': True},
                            {'name': 'content', 'label': 'Content Preview', 'field': 'content', 'align': 'left', 'sortable': True},
                        ]

                        # Create rows from filtered data
                        rows = []
                        for file_info in filtered:
                            content_preview = file_info['content'][:400] + '...' if len(file_info['content']) > 400 else file_info['content']
                            rows.append({
                                'filename': file_info['filename'],
                                # table cell gets a preview, but we also provide full content under 'content_full'
                                'content': content_preview,
                                'content_full': file_info['content'],
                                'path': file_info['path'],
                            })

                        # Store rows for click handler
                        rows_for_click = rows

                        # Create robust row click handler (handles varying event arg shapes)
                        on_row_click_handler = create_file_row_click_handler(rows_for_click, open_file)

                        # Create sortable table
                        create_sortable_table(
                            table_container,
                            columns,
                            rows,
                            row_key='filename',
                            on_row_click=on_row_click_handler,
                            tip_message='Tip: Enter a search term to filter files by content. Click any row to open the file.'
                        )

                    # Update result count
                    result_count_label.text = f'Showing {len(filtered)} of {len(file_data)} files'

                # Initial table render
                update_table('')

                # Update table when search input changes
                def on_search_change(e):
                    search_term = e.args if isinstance(e.args, str) else search_input.value
                    update_table(search_term)

                search_input.on('update:modelValue', on_search_change)
                search_input.on('blur', lambda: update_table(search_input.value))

    logger.debug("Searchable file list rendered successfully")

