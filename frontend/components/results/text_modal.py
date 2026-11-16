"""Modal dialog for displaying full text or markdown documents."""

from __future__ import annotations

from nicegui import ui

from frontend.design_tokens import Design


def open_text_markdown_modal(filename: str, body: str) -> None:
    """Open a scrollable modal dialog showing full document text."""
    text = body if body is not None else ""
    with (
        ui.dialog() as dialog,
        ui.card().classes(
            "max-w-[92vw] w-[min(56rem,92vw)] max-h-[90vh] flex flex-col p-4 gap-3"
        ),
    ):
        ui.label(filename or "Document").classes(
            "text-lg font-semibold shrink-0 text-zinc-900"
        )
        with ui.scroll_area().classes(
            "w-full min-h-[50vh] max-h-[75vh] border border-zinc-200 rounded-lg bg-white"
        ):
            if text.strip():
                ui.textarea(value=text).props(
                    "readonly outlined dense input-class=font-mono"
                ).classes("w-full min-h-[48vh]").style("white-space: pre-wrap")
            else:
                ui.label("No content").classes("text-zinc-500 italic p-4")
        with ui.row().classes("justify-end shrink-0"):
            ui.button("Close", on_click=dialog.close).classes(Design.BTN_MEDIUM_GRAY)
    dialog.open()
