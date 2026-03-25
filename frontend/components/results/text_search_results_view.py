"""
Renders text-embedding search API JSON as a readable summary + table.
"""

from __future__ import annotations

import logging
from typing import Any

from nicegui import ui

from frontend.components.results.table_helpers import create_sortable_table

logger = logging.getLogger(__name__)


def _pick(d: dict, *keys: str, default: Any = "") -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def is_text_search_payload(data: Any) -> bool:
    """True if JSON looks like text_embeddings /search output."""
    if not isinstance(data, dict):
        return False
    if "error" in data and "results" not in data:
        return False
    if "query" not in data or "results" not in data:
        return False
    if not isinstance(data.get("results"), list):
        return False
    return True


def render_text_search_json(container: ui.element, data: dict, title: str = "Text Search Results") -> None:
    """Show query summary, optional guidance, and a sortable results table."""
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
                    preview = str(_pick(r, "matching_text", "matchingtext", default=""))
                    if len(preview) > 280:
                        preview = preview[:277] + "…"
                    rows.append(
                        {
                            "id": rid,
                            "match": "Yes" if is_match else "No",
                            "similarity": sim_s,
                            "path": path,
                            "preview": preview,
                        }
                    )

                columns = [
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
                    {
                        "name": "preview",
                        "label": "Matching text",
                        "field": "preview",
                        "align": "left",
                        "sortable": False,
                    },
                ]

                with ui.scroll_area().classes("w-full max-h-[70vh]"):
                    table_holder = ui.column().classes("w-full min-w-0")
                    create_sortable_table(
                        table_holder,
                        columns,
                        rows,
                        row_key="id",
                        show_row_labels=False,
                        tip_message="Sort columns by clicking headers. Match = similarity ≥ threshold.",
                    )
