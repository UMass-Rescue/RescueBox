import logging

from nicegui import ui

from frontend.design_tokens import Design

logger = logging.getLogger(__name__)


async def show_case_notes_dialog() -> str | None:
    """Show case notes modal and await user input."""
    with ui.dialog() as dialog, ui.card().classes(Design.PANEL_SHELL_CARD_MD):
        with ui.row().classes(Design.PANEL_SHELL_HEADER):
            ui.label("Case Notes").classes(Design.PANEL_SHELL_HEADER_TITLE)

        with ui.column().classes("px-6 pt-4 pb-2 gap-2"):
            ui.label("Add notes for this job (optional)").classes(
                "text-zinc-600 text-sm"
            )
            textarea = ui.textarea(
                placeholder="e.g. case ID, examiner name, purpose...",
            ).classes(f"w-full min-h-24 {Design.INPUT_OUTLINED}")

        with ui.row().classes(f"{Design.PANEL_SHELL_FOOTER} justify-end flex-wrap"):
            ui.button(
                "Cancel", color=None, on_click=lambda: dialog.submit(None)
            ).classes(Design.BTN_MEDIUM_GRAY)
            ui.button(
                "Submit Job",
                color=None,
                on_click=lambda: dialog.submit((textarea.value or "").strip()),
            ).classes("rb-brand-primary text-white rounded-xl px-4 py-2")

    dialog.open()
    result = await dialog
    return result
