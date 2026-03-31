import logging
from nicegui import ui
from typing import List, Dict, Any, Callable

from frontend.components.results.table_helpers import create_sortable_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_batch_file_table(container: ui.element, columns: List[Dict[str, Any]], rows: List[Dict[str, Any]], on_row_click: Callable, tip_message: str = '') -> None:
    """
    Render a sortable batch file table inside a card and expose plain labels for tests.
    """
    try:
        with container:
            table_card = ui.card().classes('bg-white p-4')
            with table_card:
                table_column = ui.column()
                create_sortable_table(
                    table_column,
                    columns,
                    rows,
                    row_key='path',
                    on_row_click=on_row_click,
                    show_row_labels=False,
                    tip_message=tip_message
                )
    except Exception as e:
        logger.exception("Error rendering batch file table: %s", e)
        with container:
            ui.label(f'Error rendering table: {e}').classes('text-red-600')

