"""Text, markdown, and batch-text response renderers."""

from __future__ import annotations

import json
from typing import Any

from nicegui import ui

from .batch_text import render_batch_text
from .image_summary import render_image_summary_json
from .text_modal import open_text_markdown_modal
from .text_search import render_searchable_file_list, render_text_search_json


def render_markdown(container: Any, response: Any) -> None:
    """Render a response object containing raw markdown text."""
    with container, ui.card().classes("w-full p-4"):
        ui.label("📄 Markdown Result").classes("font-bold mb-2")
        ui.markdown(response.value).classes("prose prose-sm max-w-none")


def render_text(container: Any, response: Any) -> None:
    """Main dispatcher for text responses (detecting JSON search, image summaries, or markdown)."""
    val = response.value if hasattr(response, "value") else response.get("value", "")
    title = getattr(response, "title", "Text Result") or "Text Result"
    try:
        data = json.loads(val)
        if isinstance(data, dict):
            if data.get("results") or data.get("query"):
                return render_text_search_json(container, data, title=title)
            if data.get("image_summary"):
                return render_image_summary_json(container, data)
        if isinstance(data, list) and all(isinstance(x, str) for x in data):
            return render_searchable_file_list(container, data, title)
    except (json.JSONDecodeError, TypeError):
        pass
    with (
        container,
        ui.card().classes(
            "w-full p-0 shadow-lg border rounded-xl overflow-hidden bg-white"
        ),
    ):
        with ui.row().classes("w-full p-4 items-center border-b border-zinc-100"):
            ui.label("Text Result").classes("text-lg font-bold text-zinc-900")
            if title and title != "Text Result":
                ui.label(f"• {title}").classes(
                    "ml-2 opacity-90 text-sm font-medium text-zinc-700"
                )
        with ui.scroll_area().classes("w-full h-96"):
            with ui.column().classes("w-full p-6"):
                ui.markdown(val).classes(
                    "prose prose-sm max-w-none text-zinc-900 leading-relaxed"
                )
    return None


__all__ = [
    "open_text_markdown_modal",
    "render_batch_text",
    "render_markdown",
    "render_searchable_file_list",
    "render_text",
    "render_text_search_json",
]
