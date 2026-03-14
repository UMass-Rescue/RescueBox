from nicegui import ui
import logging
from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def show_validation_dialog(primary_error: str, additional_errors: List[str] | None = None) -> ui.dialog:
    """
    Show a modal validation dialog listing primary and additional errors.
    Returns the dialog instance (already opened).
    """
    with ui.dialog() as error_dialog:
        with ui.card().classes('max-w-md'):
            ui.label('Validation Error').classes('text-lg font-bold text-red-600 mb-4')
            ui.label(primary_error).classes('mb-4')
            if additional_errors:
                ui.label('Additional errors:').classes('font-semibold mb-2')
                for additional_error in additional_errors:
                    ui.label(f'• {additional_error}').classes('mb-1')
            ui.button('OK', on_click=error_dialog.close).classes('mt-4')
    error_dialog.open()
    logger.debug("Validation dialog opened with primary_error: %s", primary_error)
    return error_dialog

