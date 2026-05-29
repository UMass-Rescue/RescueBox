import logging
import os
from pathlib import Path
from typing import Any, List, Dict
from nicegui import ui

from frontend.components.results.table_helpers import (
    create_sortable_table,
    resolve_table_row_index,
)
from frontend.components.results.image_summary_results_view import (
    _ensure_image_summary_modal_css,
)
from frontend.components.results.results_utils import open_text_markdown_modal

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

    _ensure_image_summary_modal_css()

    with container:
        with ui.card().classes('w-full bg-white border border-zinc-300 rounded-xl p-4 shadow-sm'):
            with ui.column().classes('gap-3 w-full'):
                ui.label(f'{title} ({len(file_data)} files)').classes(
                    'text-lg font-bold text-zinc-900'
                )

                with ui.element('div').classes(
                    'w-full rounded-lg border-2 border-[#505759] bg-white p-3 shadow-sm'
                ):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('search', size='1.5rem').classes('text-[#505759] shrink-0')
                        ui.label('Search').classes(
                            'text-lg font-bold text-[#505759] tracking-tight'
                        )
                    search_input = ui.input(
                        placeholder='Type to filter rows by content (e.g. blue car)',
                        value='',
                    ).classes('w-full rb-image-summary-search-field').props(
                        'clearable outlined dense'
                    )

                # Container for table that will be refreshed
                table_container = ui.column().classes('w-full')
                result_count_label = ui.label(
                    f'Showing {len(file_data)} of {len(file_data)} files'
                ).classes('text-sm text-zinc-600')

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

                        # Only column fields on each row — Quasar sync strips extra keys; keep full text + paths in side maps.
                        content_by_filename: Dict[str, str] = {
                            fi['filename']: fi['content'] for fi in filtered
                        }
                        path_by_filename: Dict[str, str] = {
                            fi['filename']: fi['path'] for fi in filtered
                        }

                        rows = []
                        for file_info in filtered:
                            content_preview = (
                                file_info['content'][:400] + '...'
                                if len(file_info['content']) > 400
                                else file_info['content']
                            )
                            rows.append({
                                'filename': file_info['filename'],
                                'content': content_preview,
                            })

                        rows_for_click = rows

                        def on_row_click_handler(e):
                            """Open full file text in a modal (no ``/_serve`` navigation)."""
                            try:
                                fn: str | None = None
                                if len(getattr(e, 'args', ())) > 1 and isinstance(e.args[1], dict):
                                    cand = e.args[1]
                                    fn = (cand.get('filename') or cand.get('name') or '').strip() or None
                                if not fn:
                                    row_index = resolve_table_row_index(e, rows_for_click)
                                    if row_index is None:
                                        return
                                    row = rows_for_click[row_index]
                                    fn = (row.get('filename') or 'Document').strip() or 'Document'

                                body = content_by_filename.get(fn, '')
                                if not body.strip():
                                    pth = path_by_filename.get(fn)
                                    if pth and os.path.isfile(pth):
                                        try:
                                            body = Path(pth).read_text(encoding='utf-8', errors='replace')
                                        except OSError as oe:
                                            logger.warning("Re-read summary file failed %s: %s", pth, oe)
                                if not body.strip():
                                    logger.warning(
                                        "No full text for filename=%r (paths=%r)",
                                        fn,
                                        list(path_by_filename.keys()),
                                    )
                                    ui.notify(
                                        'Full text for this row could not be resolved.',
                                        type='warning',
                                        classes='rb-notify-505759',
                                    )
                                    return
                                open_text_markdown_modal(fn, body)
                            except Exception as ex:
                                logger.warning(
                                    "Error opening summary from table row click: %s", ex
                                )

                        # Create sortable table
                        create_sortable_table(
                            table_container,
                            columns,
                            rows,
                            row_key='filename',
                            on_row_click=on_row_click_handler,
                            tip_message=(
                                'Tip: Enter a search term to filter files by content. '
                                'Click any row to read the full summary in a window.'
                            ),
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

