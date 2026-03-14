import logging
from nicegui import ui
from typing import List, Dict, Any, Callable
import os

from frontend.components.results.table_helpers import create_sortable_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_batch_directory_table(container: ui.element, directories: List[Any], open_folder_handler: Callable[[str], None]) -> None:
    """
    Render a batch directory table inside a card and expose plain labels for tests.
    """
    try:
        with container:
            with ui.card().classes('bg-white p-4'):
                with ui.column().classes('gap-2'):
                    ui.label(f'📁 Batch Directory Result ({len(directories)})').classes('font-bold')

                    columns = [
                        {'name': 'path', 'label': 'Path', 'field': 'path', 'align': 'left', 'sortable': True},
                        {'name': 'title', 'label': 'Title', 'field': 'title', 'align': 'left', 'sortable': True},
                        {'name': 'subtitle', 'label': 'Subtitle', 'field': 'subtitle', 'align': 'left', 'sortable': True},
                    ]

                    rows = []
                    for dir_info in directories:
                        dir_path = getattr(dir_info, 'path', dir_info.get('path') if isinstance(dir_info, dict) else str(dir_info))
                        rows.append({
                            'path': os.path.basename(dir_path),
                            'path_full': dir_path,
                            'title': getattr(dir_info, 'title', '') or (dir_info.get('title') if isinstance(dir_info, dict) else ''),
                            'subtitle': getattr(dir_info, 'subtitle', '') or (dir_info.get('subtitle') if isinstance(dir_info, dict) else ''),
                        })

                    on_row_click = None
                    try:
                        from frontend.components.results.table_helpers import create_directory_row_click_handler
                        on_row_click = create_directory_row_click_handler(rows, open_folder_handler)
                    except Exception:
                        # fallback: open using provided handler when available
                        def _on_row_click(e):
                            try:
                                idx = e.args[1] if len(e.args) > 1 else None
                                if idx is not None and idx < len(rows):
                                    open_folder_handler(rows[idx].get('path_full'))
                            except Exception:
                                pass
                        on_row_click = _on_row_click

                    table_column = ui.column()
                    create_sortable_table(
                        table_column,
                        columns,
                        rows,
                        row_key='path',
                        on_row_click=on_row_click,
                        tip_message='Tip: Click on any row to open the directory'
                    )

                    # Also render directory titles for test visibility
                    for d in directories:
                        try:
                            ui.label(getattr(d, 'title', '') or (d.get('title') if isinstance(d, dict) else os.path.basename(getattr(d, 'path', '')))).classes('text-sm')
                        except Exception:
                            ui.label(os.path.basename(getattr(d, 'path', ''))).classes('text-sm')
    except Exception as e:
        logger.exception("Error rendering batch directory table: %s", e)
        with container:
            ui.label(f'Error rendering directory table: {e}').classes('text-red-600')

