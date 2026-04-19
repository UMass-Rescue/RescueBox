"""
Case Notes Dialog

Shows a modal for the user to enter job-specific case notes before submitting.
Returns the notes text when user clicks Submit, or None if cancelled.
"""

import logging
from typing import Optional

from nicegui import ui

from frontend.design_tokens import Design

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def show_case_notes_dialog() -> Optional[str]:
    """
    Show case notes modal and await user input.

    Returns:
        str: Notes text (may be empty) if user clicks Submit Job
        None: If user clicks Cancel or closes the dialog (backdrop/ESC)
    """
    with ui.dialog() as dialog, ui.card().classes(Design.PANEL_SHELL_CARD_MD):
        with ui.row().classes(Design.PANEL_SHELL_HEADER):
            ui.label("Case Notes").classes(Design.PANEL_SHELL_HEADER_TITLE)

        with ui.column().classes("px-6 pt-4 pb-2 gap-2"):
            ui.label("Add notes for this job (optional)").classes("text-zinc-600 text-sm")
            textarea = ui.textarea(
                placeholder="e.g. case ID, examiner name, purpose...",
            ).classes(f"w-full min-h-24 {Design.INPUT_OUTLINED}")

        with ui.row().classes(f"{Design.PANEL_SHELL_FOOTER} justify-end flex-wrap"):
            ui.button("Cancel", on_click=lambda: dialog.submit(None)).classes(
                Design.BTN_MEDIUM_GRAY
            )
            ui.button(
                "Submit Job",
                on_click=lambda: dialog.submit((textarea.value or "").strip()),
            ).classes("rb-brand-primary text-white rounded-xl px-4 py-2")

    dialog.open()
    logger.debug("Case notes dialog opened")
    result = await dialog
    logger.debug("Case notes dialog closed, result length: %d", len(result) if result else 0)
    return result
