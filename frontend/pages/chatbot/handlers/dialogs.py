from __future__ import annotations

import asyncio
from typing import Optional

from nicegui import ui

from frontend.design_tokens import Design


async def show_case_notes_dialog() -> Optional[str]:
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    with ui.dialog() as dialog, ui.card().classes(Design.PANEL_SHELL_CARD_NARROW):
        with ui.row().classes(Design.PANEL_SHELL_HEADER):
            with ui.row().classes("items-center gap-2"):
                ui.label("Job Submission Details").classes(
                    Design.PANEL_SHELL_HEADER_TITLE
                )
            ui.button(
                color=None,
                on_click=lambda: (future.set_result(None), dialog.close()),
            ).props("flat round dense").classes(Design.PANEL_SHELL_HEADER_ICON)

        with ui.column().classes(Design.PANEL_SHELL_BODY + " gap-4"):
            ui.label("Add optional notes for the case file:").classes(
                "text-sm text-slate-500 font-medium"
            )
            notes = (
                ui.textarea(label="Case Notes")
                .classes("w-full rb-case-notes-field")
                .props("outlined")
            )

        with ui.row().classes(Design.PANEL_SHELL_FOOTER + " justify-end"):
            ui.button(
                "Skip & Submit",
                color=None,
                on_click=lambda: (future.set_result(""), dialog.close()),
            ).classes(Design.BTN_MEDIUM_GRAY).props("outline")
            ui.button(
                "Submit with Notes",
                color=None,
                on_click=lambda: (future.set_result(notes.value), dialog.close()),
            ).classes(Design.BTN_PRIMARY)
    dialog.open()
    return await future
