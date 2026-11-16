"""Batch text and multi-document transcription card renderer."""

from __future__ import annotations

from typing import Any

from nicegui import ui


def render_batch_text(container: Any, response: Any) -> None:
    """Render a collection of transcription items or extracted text blocks."""
    texts = getattr(response, "texts", [])
    if not texts:
        with container:
            ui.label("No text found").classes("text-zinc-500 italic")
        return
    with (
        container,
        ui.card().classes(
            "w-full p-0 shadow-sm border rounded-xl overflow-hidden bg-white"
        ),
    ):
        with ui.row().classes(
            "w-full px-4 py-3 items-center gap-2 border-b border-zinc-200 bg-gradient-to-r from-zinc-50 to-white"
        ):
            ui.label("Transcription").classes("text-sm font-semibold text-[#505759]")
            ui.label(f"{len(texts)} file(s)").classes(
                "text-xs text-zinc-500 ml-auto tabular-nums"
            )
        with ui.column().classes("w-full p-4"):
            with ui.scroll_area().classes("w-full h-[60vh]"):
                for i, t in enumerate(texts, 1):
                    with ui.column().classes(
                        "w-full min-w-0 gap-2 pb-4 border-b border-zinc-100 last:border-b-0 last:pb-0 mb-4"
                    ):
                        ui.label("Source").classes(
                            "text-xs font-medium text-zinc-500 uppercase tracking-wide"
                        )
                        ui.label(
                            getattr(t, "title", f"Item {i}") or f"Item {i}"
                        ).classes("text-sm font-semibold text-zinc-900 break-all")
                        with ui.scroll_area().classes(
                            "w-full max-h-80 rounded-lg bg-zinc-50 ring-1 ring-zinc-200"
                        ):
                            ui.label(getattr(t, "value", "") or "").classes(
                                "text-sm text-zinc-800 whitespace-pre-wrap leading-relaxed p-3 block"
                            )
