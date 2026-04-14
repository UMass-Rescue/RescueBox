"""
Renders text-embedding search API JSON as a readable summary + table.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from nicegui import ui

from frontend.components.results.table_helpers import (
    create_sortable_table,
    resolve_table_row_index,
)
from frontend.utils.pipeline_index_context import get_pipeline_index_ids
from frontend.database.pipeline_job_index_db import lookup_source_image

logger = logging.getLogger(__name__)

# Preview cap for row-click dialog (forensic folders may have huge exports)
_MAX_FILE_PREVIEW_BYTES = 2 * 1024 * 1024

_TEXT_LIKE_EXT = frozenset({
    ".txt", ".text", ".md", ".log", ".csv", ".json", ".xml", ".html", ".htm",
})


def _is_text_like_path(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in _TEXT_LIKE_EXT or ext == ""


def _read_file_preview(path: str) -> str:
    try:
        with open(path, "rb") as f:
            data = f.read(_MAX_FILE_PREVIEW_BYTES + 1)
        if len(data) > _MAX_FILE_PREVIEW_BYTES:
            text = data[:_MAX_FILE_PREVIEW_BYTES].decode("utf-8", errors="replace")
            text += "\n\n*(Preview truncated — file exceeds size limit.)*"
        else:
            text = data.decode("utf-8", errors="replace")
        return text
    except OSError as e:
        return f"*(Could not read file: {e})*"


def _open_text_search_row_preview(path: str) -> None:
    """Large markdown preview for text-like files; otherwise use existing file opener."""
    if not path or not os.path.isfile(path):
        ui.notify("File not found or not a file.", type="warning")
        return
    if not _is_text_like_path(path):
        from frontend.components.results.results_utils import open_file
        open_file(path)
        return

    body = _read_file_preview(path)
    name = os.path.basename(path)
    with ui.dialog() as dialog, ui.card().classes(
        "w-full max-w-4xl p-0 gap-0 overflow-hidden"
    ):
        with ui.row().classes(
            "w-full px-4 py-3 items-center justify-between bg-slate-100 border-b border-slate-200"
        ):
            ui.label(name).classes("text-xl font-semibold text-slate-800 truncate")
            ui.button(icon="close", on_click=dialog.close).props("flat dense round")
        ui.label(path).classes("text-sm font-mono text-slate-500 px-4 pb-2 break-all")
        with ui.scroll_area().classes("w-full max-h-[80vh] px-4 pb-4"):
            ui.markdown(body).classes("text-lg leading-relaxed w-full max-w-none")
        with ui.row().classes("w-full justify-end px-4 py-3 border-t border-slate-200 bg-slate-50"):
            ui.button("Close", on_click=dialog.close).props("outline")
    dialog.open()


def _pick(d: dict, *keys: str, default: Any = "") -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def is_text_search_payload(data: Any) -> bool:
    """True if JSON looks like text_embeddings /search or image_embeddings /search_images output."""
    if not isinstance(data, dict):
        return False
    if "error" in data and "results" not in data:
        return False
    if "query" not in data or "results" not in data:
        return False
    if not isinstance(data.get("results"), list):
        return False
    return True


def _results_have_matching_text(results: list) -> bool:
    """Text-embedding search rows include chunk text; image search rows do not."""
    for r in results:
        if not isinstance(r, dict):
            continue
        mt = _pick(r, "matching_text", "matchingtext", default="")
        if str(mt).strip():
            return True
    return False


def render_text_search_json(container: ui.element, data: dict, title: str = "Text Search Results") -> None:
    """Show query summary, optional guidance, and a sortable results table."""
    puid, prid = get_pipeline_index_ids()
    query = _pick(data, "query")
    model = _pick(data, "model")
    top_k = _pick(data, "top_k", "topk")
    min_sim = _pick(data, "min_similarity", "minsimilarity")
    guidance = _pick(data, "similarity_guidance", "similarityguidance")
    results = data.get("results") or []

    if data.get("error"):
        with container:
            ui.label(str(data["error"])).classes("text-red-600")
        return

    with container:
        with ui.card().classes(
            "w-full min-w-0 max-w-full self-stretch bg-gradient-to-br from-blue-50 to-indigo-50 "
            "border-2 border-blue-300 rounded-xl shadow-lg overflow-hidden"
        ):
            with ui.row().classes(
                "w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white p-4 items-center"
            ):
                ui.icon("search", size="1.5rem").classes("mr-3")
                ui.label(title).classes("text-lg font-bold")

            with ui.column().classes("w-full p-4 gap-3"):
                with ui.column().classes("gap-1 text-sm text-gray-800"):
                    ui.label(f"Query: {query}").classes("font-medium")
                    if model:
                        ui.label(f"Model: {model}").classes("text-gray-600")
                    meta_bits = []
                    if top_k != "":
                        meta_bits.append(f"Top {top_k}")
                    if min_sim != "":
                        meta_bits.append(f"Match threshold ≥ {min_sim}")
                    if meta_bits:
                        ui.label(" · ".join(meta_bits)).classes("text-gray-600")

                if guidance:
                    ui.label(str(guidance)).classes("text-xs text-gray-600 bg-white/60 rounded p-2 border border-blue-100")

                if not results:
                    ui.label("No results.").classes("text-gray-500 italic")
                    return

                show_text_snippet = _results_have_matching_text(results)

                rows: list[dict] = []
                for i, r in enumerate(results):
                    if not isinstance(r, dict):
                        continue
                    rid = _pick(r, "id", default=i)
                    sim = _pick(r, "similarity")
                    try:
                        sim_s = f"{float(sim):.4f}"
                    except (TypeError, ValueError):
                        sim_s = str(sim)
                    is_match = _pick(r, "is_match", "ismatch", default=False)
                    if isinstance(is_match, str):
                        is_match = is_match.lower() in ("true", "1", "yes")
                    path = str(_pick(r, "path", default=""))
                    row_dict: dict = {
                        "id": rid,
                        "match": "Yes" if is_match else "No",
                        "similarity": sim_s,
                        "path": path,
                    }
                    if show_text_snippet:
                        preview = str(_pick(r, "matching_text", "matchingtext", default=""))
                        if len(preview) > 280:
                            preview = preview[:277] + "…"
                        row_dict["preview"] = preview
                    if puid and prid and path:
                        simg = lookup_source_image(puid, prid, path)
                        if simg:
                            row_dict["_source_image"] = simg
                    rows.append(row_dict)

                show_source_image = any(bool(r.get("_source_image")) for r in rows)

                columns: list[dict] = [
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
                ]
                if show_source_image:
                    columns.append(
                        {
                            "name": "source_thumb",
                            "label": "Source image",
                            "field": "source_thumb",
                            "align": "center",
                            "sortable": False,
                        }
                    )
                columns.append(
                    {
                        "name": "path",
                        "label": "File",
                        "field": "path",
                        "align": "left",
                        "sortable": True,
                    }
                )
                if show_text_snippet:
                    columns.append(
                        {
                            "name": "preview",
                            "label": "Matching text",
                            "field": "preview",
                            "align": "left",
                            "sortable": False,
                        }
                    )
                display_rows: list[dict] = []
                for r in rows:
                    dr = {k: v for k, v in r.items() if k != "_source_image"}
                    if show_source_image:
                        simg = r.get("_source_image")
                        dr["source_thumb"] = os.path.basename(simg) if simg else "—"
                    display_rows.append(dr)

                extra_src = ""
                if show_source_image:
                    extra_src = (
                        " Source image column: original picture for each summary .txt (pipeline index)."
                    )

                tip = (
                    (
                        "Sort columns by clicking headers. Match = similarity ≥ threshold. "
                        "Click a row to open the full file (large markdown preview for text)."
                    )
                    + extra_src
                    if show_text_snippet
                    else (
                        (
                            "Sort columns by clicking headers. Match = similarity ≥ threshold. "
                            "Click a row to open the file."
                        )
                        + extra_src
                    )
                )

                def _on_row_click(e):
                    idx = resolve_table_row_index(e, display_rows)
                    if idx is None:
                        return
                    p = str(display_rows[idx].get("path") or "").strip()
                    if p:
                        _open_text_search_row_preview(p)

                with ui.scroll_area().classes("w-full max-h-[70vh]"):
                    table_holder = ui.column().classes("w-full min-w-0")
                    create_sortable_table(
                        table_holder,
                        columns,
                        display_rows,
                        row_key="id",
                        show_row_labels=False,
                        tip_message=tip,
                        on_row_click=_on_row_click,
                        table_extra_classes="text-base",
                        tip_message_classes="text-sm text-gray-600 mt-3",
                    )
