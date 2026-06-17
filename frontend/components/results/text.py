"""Text, markdown, and batch-text response renderers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from nicegui import ui

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.design_tokens import Design

from .image_summary import (
    ensure_image_summary_modal_css,
    render_image_summary_json,
)
from .serve_paths import open_file
from .table_helpers import (
    create_sortable_table,
    file_search_result_row,
    filename_sortable_columns,
    resolve_row_idx,
)


def open_text_markdown_modal(filename: str, body: str) -> None:
    text = body if body is not None else ""
    with ui.dialog() as dialog, ui.card().classes(
        "max-w-[92vw] w-[min(56rem,92vw)] max-h-[90vh] flex flex-col p-4 gap-3"
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


def _pick(d: dict, *keys: str, default: Any = "") -> Any:
    for k in keys:
        if k in d:
            return d[k]
    return default


def render_text_search_json(container, data, title="Text Search Results"):
    query, model, results = (
        _pick(data, "query"),
        _pick(data, "model"),
        data.get("results") or [],
    )
    if data.get("error"):
        with container:
            ui.label(str(data["error"])).classes("text-red-700")
        return
    if not results:
        with container:
            ui.label("No results.").classes("text-zinc-500 italic")
        return

    rows = []
    show_text_snippet = any(
        str(_pick(r, "matching_text", "matchingtext")).strip()
        for r in results
        if isinstance(r, dict)
    )
    for i, r in enumerate(results):
        if not isinstance(r, dict):
            continue
        sim = _pick(r, "similarity", default=0)
        row = {
            "id": _pick(r, "id", default=i),
            "match": "Yes" if _pick(r, "is_match", default=False) else "No",
            "similarity": (
                f"{float(sim):.4f}" if isinstance(sim, (int, float)) else str(sim)
            ),
            "path": str(_pick(r, "path")),
        }
        if show_text_snippet:
            preview = str(_pick(r, "matching_text", "matchingtext"))
            row["preview"] = preview[:277] + "…" if len(preview) > 280 else preview
        rows.append(row)

    cols = [
        {
            "name": "match",
            "label": "Match",
            "field": "match",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "similarity",
            "label": "Similarity",
            "field": "similarity",
            "align": "right",
            "sortable": True,
        },
        {
            "name": "path",
            "label": "File",
            "field": "path",
            "align": "left",
            "sortable": True,
        },
    ]
    if show_text_snippet:
        cols.append(
            {
                "name": "preview",
                "label": "Matching Text",
                "field": "preview",
                "align": "left",
            }
        )

    with container, ui.card().classes(
        "w-full min-w-0 max-w-full flex flex-col rounded-3xl shadow-xl "
        "border border-zinc-100 p-0 overflow-hidden bg-white"
    ):
        with ui.row().classes(Design.PANEL_SHELL_HEADER):
            ui.label(title).classes(Design.PANEL_SHELL_HEADER_TITLE)
        with ui.column().classes("w-full p-4 gap-3"):
            with ui.column().classes("gap-1 text-sm text-zinc-800"):
                ui.label(f"Query string: {query}").classes("font-medium text-zinc-900")
                if model:
                    ui.label(f"Plugin: {model}").classes("text-zinc-600")

            def _on_click(e):
                idx = resolve_row_idx(e, rows)
                if idx is not None and rows[idx]["path"]:
                    p = rows[idx]["path"]
                    if os.path.isfile(p):
                        try:
                            body = Path(p).read_text(encoding="utf-8", errors="replace")
                        except UI_RENDER_ERRORS:
                            body = f"Could not read file at {p}"
                        open_text_markdown_modal(os.path.basename(p), body)
                    else:
                        open_file(p)

            with ui.scroll_area().classes("w-full max-h-[70vh]"):
                create_sortable_table(
                    ui.column().classes("w-full"),
                    cols,
                    rows,
                    row_key="id",
                    on_row_click=_on_click,
                    tip_message="Sort columns by clicking headers. Click a row to open full preview.",
                    table_extra_classes="text-base",
                )


def render_searchable_file_list(container, file_paths, title):
    file_data = []
    for fp in file_paths:
        if os.path.exists(fp):
            try:
                content = Path(fp).read_text(encoding="utf-8", errors="replace")
                file_data.append(file_search_result_row(fp, content))
            except UI_RENDER_ERRORS:
                pass
    if not file_data:
        with container:
            ui.label("No valid files found").classes("text-red-600")
        return
    ensure_image_summary_modal_css()
    with container, ui.card().classes(
        "w-full bg-white border border-zinc-300 rounded-xl p-4 shadow-sm"
    ):
        ui.label(f"{title} ({len(file_data)} files)").classes(
            "text-lg font-bold text-zinc-900 mb-4"
        )
        with ui.element("div").classes(
            "w-full rounded-lg border-2 border-[#505759] bg-white p-3 shadow-sm mb-4"
        ):
            with ui.row().classes("items-center gap-2 mb-2"):
                ui.icon("search", size="1.5rem").classes("text-[#505759]")
                ui.label("Search").classes("text-lg font-bold text-[#505759]")
            search_input = (
                ui.input(placeholder="Filter by content...")
                .classes("w-full rb-image-summary-search-field")
                .props("clearable outlined dense")
            )
        table_container = ui.column().classes("w-full")

        def update_table(search_term=""):
            search_lower = search_term.lower().strip()
            filtered = (
                [f for f in file_data if search_lower in f["content_lower"]]
                if search_lower
                else file_data
            )
            table_container.clear()
            cols = [
                *filename_sortable_columns(),
                {
                    "name": "content",
                    "label": "Preview",
                    "field": "content",
                    "align": "left",
                    "sortable": True,
                },
            ]
            rows = [
                {
                    "filename": f["filename"],
                    "content": (
                        f["content"][:400] + "..."
                        if len(f["content"]) > 400
                        else f["content"]
                    ),
                    "path": f["path"],
                }
                for f in filtered
            ]

            def _on_click(e):
                idx = resolve_row_idx(e, rows)
                if idx is not None:
                    row = rows[idx]
                    open_text_markdown_modal(
                        row["filename"],
                        Path(row["path"]).read_text(encoding="utf-8", errors="replace"),
                    )

            create_sortable_table(
                table_container,
                cols,
                rows,
                row_key="filename",
                on_row_click=_on_click,
                tip_message="Enter a search term to filter. Click any row for full preview.",
            )

        search_input.on("update:modelValue", lambda e: update_table(e.args))
        update_table("")


def render_batch_text(container, response):
    texts = getattr(response, "texts", [])
    if not texts:
        with container:
            ui.label("No text found").classes("text-zinc-500 italic")
        return
    with container, ui.card().classes(
        "w-full p-0 shadow-sm border rounded-xl overflow-hidden bg-white"
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


def render_markdown(container, response):
    with container, ui.card().classes("w-full p-4"):
        ui.label("📄 Markdown Result").classes("font-bold mb-2")
        ui.markdown(response.value).classes("prose prose-sm max-w-none")


def render_text(container, response):
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
    with container, ui.card().classes(
        "w-full p-0 shadow-lg border rounded-xl overflow-hidden bg-white"
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
