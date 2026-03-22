"""
Case Notes Dialog

Shows a modal for the user to enter job-specific case notes before submitting.
Returns the notes text when user clicks Submit, or None if cancelled.
"""

import logging
from typing import Optional
from nicegui import ui

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def show_case_notes_dialog() -> Optional[str]:
    """
    Show case notes modal and await user input.

    Returns:
        str: Notes text (may be empty) if user clicks Submit Job
        None: If user clicks Cancel or closes the dialog (backdrop/ESC)
    """
    with ui.dialog() as dialog, ui.card().classes('max-w-md'):
        ui.label('Case Notes').classes('text-lg font-bold mb-4')
        ui.label('Add notes for this job (optional)').classes('text-gray-600 text-sm mb-2')
        textarea = ui.textarea(
            placeholder='e.g. case ID, examiner name, purpose...'
        ).classes('w-full min-h-24')

        with ui.row().classes('mt-4 gap-2'):
            ui.button(
                'Cancel',
                on_click=lambda: dialog.submit(None)
            ).classes('bg-gray-300')
            ui.button(
                'Submit Job',
                on_click=lambda: dialog.submit((textarea.value or '').strip())
            ).classes('bg-green-600 text-white')

    dialog.open()
    logger.debug("Case notes dialog opened")
    result = await dialog
    logger.debug("Case notes dialog closed, result length: %d", len(result) if result else 0)
    return result
