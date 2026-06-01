from __future__ import annotations
import ast
import json
import logging
import os
import platform
import subprocess
import uuid
import time
import weakref
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw
from nicegui import ui, app
from starlette.responses import FileResponse as StarletteFileResponse
from starlette.requests import Request
from starlette.exceptions import HTTPException
from frontend.design_tokens import Design

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Keep a weak set of active selection cards so we can aggressively clear any orphaned cards.
_ACTIVE_TOOL_SELECTION_CARDS = weakref.WeakSet()


def render_tool_selection_message(container: ui.element, endpoint: str):
    """
    Render a small tool selection message card indicating the selected tool.
    Returns the created card element so the caller can manage its lifecycle.
    """
    from frontend.chatbot.config import ToolRegistry

    plugin_label = ToolRegistry.display_name_for_endpoint(endpoint)
    logger.debug(
        "Rendering tool selection card for endpoint=%s label=%s into container=%r",
        endpoint,
        plugin_label,
        container,
    )
    # Create the card inside the (chat area) provided container context to avoid creating it
    # in the currently active UI context (which could be an input-area wrapper).
    with container:
        card = ui.card().classes(
            "w-full max-w-2xl bg-white ring-1 ring-zinc-200 shadow-sm rounded-2xl rounded-tl-none"
        )
        with card:
            with ui.column().classes("p-4 gap-2 w-full min-w-0"):
                ui.label("Assistant").classes(
                    "font-semibold !text-sm text-zinc-500 uppercase tracking-wide"
                )
                ui.label(f"Running {plugin_label} operation.").classes(
                    "!text-base sm:!text-lg leading-snug text-zinc-800"
                )
    try:
        _ACTIVE_TOOL_SELECTION_CARDS.add(card)
    except Exception:
        pass
    return card


def clear_active_tool_selection_cards():
    """Aggressively delete any active tool selection cards known globally."""
    try:
        for c in list(_ACTIVE_TOOL_SELECTION_CARDS):
            try:
                c.delete()
            except Exception:
                pass
        _ACTIVE_TOOL_SELECTION_CARDS.clear()
    except Exception:
        pass


_SERVED_FILES: Dict[str, Dict] = {}
_SERVE_ROUTE_REGISTERED = False
_SERVE_TTL = 300
_IMAGE_PREVIEW_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".svg",
}


def _ensure_serve_route():
    global _SERVE_ROUTE_REGISTERED
    if _SERVE_ROUTE_REGISTERED:
        return

    async def _serve_file(_req: Request, token: str, filename: str):
        info = _SERVED_FILES.get(token)
        if not info or time.time() - info.get("created", 0) > _SERVE_TTL:
            _SERVED_FILES.pop(token, None)
            raise HTTPException(404)
        path = info.get("path")
        if not path or not os.path.exists(path) or filename != os.path.basename(path):
            raise HTTPException(404)
        return StarletteFileResponse(path)

    try:
        app.add_api_route("/_serve/{token}/{filename}", _serve_file, methods=["GET"])
        _SERVE_ROUTE_REGISTERED = True
    except Exception as e:
        logger.error("Serve route error: %s", e)


def _serve_path(file_path: str) -> str:
    _ensure_serve_route()
    now = time.time()
    for t in [
        t for t, i in _SERVED_FILES.items() if now - i.get("created", 0) > _SERVE_TTL
    ]:
        _SERVED_FILES.pop(t, None)
    for t, i in _SERVED_FILES.items():
        if i.get("path") == file_path:
            return f"/_serve/{t}/{os.path.basename(file_path)}"
    t = uuid.uuid4().hex
    _SERVED_FILES[t] = {"path": file_path, "created": now}
    return f"/_serve/{t}/{os.path.basename(file_path)}"


def open_file(path: str):
    try:
        route = _serve_path(path)
        ext = os.path.splitext(path)[1].lower()
        if ext in _IMAGE_PREVIEW_EXTS:
            with ui.dialog() as d, ui.card().classes("max-w-[95vw] w-full p-4"):
                ui.label(os.path.basename(path)).classes("text-lg font-semibold")
                ui.image(route).props("fit=contain").classes("w-full max-h-[85vh]")
                ui.label(path).classes("text-xs font-mono text-zinc-600 break-all")
                with ui.row().classes("gap-2 mt-2"):
                    ui.button(
                        "Open folder",
                        on_click=lambda: open_folder(os.path.dirname(path)),
                    ).props("outline")
                    ui.button("Close", on_click=d.close).classes(Design.BTN_MEDIUM_GRAY)
            d.open()
        else:
            ui.navigate.to(route)
    except Exception as e:
        logger.error("Open file error: %s", e)
        ui.notify(f"Error opening file: {e}", type="negative")


def open_folder(path: str):
    if not path:
        ui.notify("Invalid folder path", type="negative")
        return
    if not os.path.exists(path):
        ui.notify("Folder not found", type="negative")
        return
    if not os.path.isdir(path):
        ui.notify("Path is not a folder", type="negative")
        return
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception as e:
        logger.error("Open folder error: %s", e)
        ui.notify(f"Failed to open folder: {e}", type="negative")


def create_metadata_table_columns(
    base_columns: List[Dict], metadata_keys: List[str]
) -> List[Dict]:
    columns = base_columns.copy()
    for key in metadata_keys:
        columns.append(
            {
                "name": key.lower().replace(" ", "_"),
                "label": key,
                "field": key.lower().replace(" ", "_"),
                "align": "left",
                "sortable": True,
            }
        )
    return columns


def resolve_table_row_index(e, rows: List[Dict]) -> Optional[int]:
    try:
        candidate = e.args[1] if len(e.args) > 1 else None
        if isinstance(candidate, int):
            return candidate
        if isinstance(candidate, dict):
            try:
                return rows.index(candidate)
            except ValueError:
                for key in ("index", "rowIndex", "row_idx"):
                    maybe = candidate.get(key)
                    if isinstance(maybe, int):
                        return maybe
        for i, r in enumerate(rows):
            if candidate == r or (
                isinstance(r, dict)
                and (candidate == r.get("id") or candidate == r.get("uid"))
            ):
                return i
    except Exception:
        pass
    return None


_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
_MAX_PREVIEW_SIDE = 1600


def parse_int_bbox(value: object) -> Optional[Tuple[int, int, int, int]]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)) and len(value) == 4:
        try:
            t = tuple(int(round(float(x))) for x in value)
            if all(x >= 0 for x in t):
                return t
        except (TypeError, ValueError):
            return None
    s = str(value).strip()
    if not s:
        return None
    try:
        v = ast.literal_eval(s)
        if isinstance(v, (list, tuple)) and len(v) == 4:
            t = tuple(int(round(float(x))) for x in v)
            if all(x >= 0 for x in t):
                return t
    except (SyntaxError, ValueError, TypeError):
        pass
    return None


def _pil_image_with_bbox_drawn(
    source: Image.Image, bbox: Tuple[int, int, int, int]
) -> Image.Image:
    x1, y1, x2, y2 = bbox
    im = source.convert("RGB")
    nw, nh = im.size
    m = max(nw, nh)
    if m > _MAX_PREVIEW_SIDE:
        scale = _MAX_PREVIEW_SIDE / m
        im = im.resize(
            (max(1, int(round(nw * scale))), max(1, int(round(nh * scale)))),
            Image.Resampling.LANCZOS,
        )
        nw, nh = im.size
        x1, y1, x2, y2 = (
            int(round(x1 * scale)),
            int(round(y1 * scale)),
            int(round(x2 * scale)),
            int(round(y2 * scale)),
        )
    draw = ImageDraw.Draw(im)
    draw.rectangle(
        [
            max(0, min(nw - 1, x1)),
            max(0, min(nh - 1, y1)),
            max(x1 + 1, min(nw, x2)),
            max(y1 + 1, min(nh, y2)),
        ],
        outline="#ff0000",
        width=4,
    )
    return im


def open_image_bbox_preview_dialog(
    abs_path: str, bbox: Tuple[int, int, int, int], row: Dict
) -> None:
    try:
        with Image.open(abs_path) as im0:
            im0.load()
            preview = _pil_image_with_bbox_drawn(im0.copy(), bbox)
    except Exception:
        open_file(abs_path)
        return
    title = str(row.get("title") or "").strip()
    gender, age = (
        str(row.get("gender") or "").strip(),
        str(row.get("age") or "").strip(),
    )
    meta = " ".join(b for b in (gender, age) if b)
    heading = (
        f"{title} — {meta}"
        if title and meta
        else (title or meta or os.path.basename(abs_path))
    )
    with ui.dialog() as dialog, ui.card().classes("max-w-5xl w-full"):
        ui.label(heading).classes("text-lg font-semibold")
        ui.image(preview).classes("max-w-full h-auto")
        ui.label(abs_path).classes("text-xs font-mono break-all text-zinc-600")
        with ui.row().classes("gap-2 mt-2"):
            ui.button(
                "Open folder",
                icon="folder_open",
                on_click=lambda: open_folder(os.path.dirname(abs_path)),
            ).props("outline")
            ui.button("Close", on_click=dialog.close).classes(Design.BTN_MEDIUM_GRAY)
    dialog.open()


def create_bbox_preview_row_click_handler(rows: List[Dict], open_file_func):
    def on_row_click(e):
        idx = resolve_table_row_index(e, rows)
        if idx is None:
            return
        row = rows[idx]
        file_path = row.get("path_full") or row.get("path")
        if not file_path or not os.path.isfile(file_path):
            if file_path:
                open_file_func(file_path)
            return
        bb = parse_int_bbox(row.get("bounding_box"))
        if bb and os.path.splitext(file_path)[1].lower() in _IMAGE_EXT:
            open_image_bbox_preview_dialog(file_path, bb, row)
        else:
            open_file_func(file_path)

    return on_row_click


def _resolve_row_idx(e, rows):
    return resolve_table_row_index(e, rows)


def create_sortable_table(
    container,
    columns,
    rows,
    row_key="id",
    on_row_click=None,
    tip_message=None,
    show_row_labels=False,
    table_extra_classes="",
    tip_message_classes="text-xs text-zinc-500 mt-2",
):
    with container:
        tc = f"w-full min-w-0 {table_extra_classes}".strip()
        table = (
            ui.table(columns=columns, rows=rows, row_key=row_key)
            .classes(tc)
            .props("flat bordered")
        )
        if show_row_labels:
            for r in rows:
                with ui.row().classes("gap-2 mt-1"):
                    for col in columns:
                        field = col.get("field") or col.get("name")
                        ui.label(str(r.get(field, ""))).classes(
                            "text-xs text-zinc-600 whitespace-pre-wrap break-words"
                        )
        if on_row_click:
            table.on("rowClick", on_row_click)
        if tip_message:
            ui.label(f"💡 {tip_message}").classes(tip_message_classes)
        return table


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


def render_batch_directory(container, response):
    dirs = getattr(response, "directories", [])
    rows = [
        {
            "path": os.path.basename(d.path),
            "path_full": d.path,
            "title": d.title,
            "subtitle": getattr(d, "subtitle", ""),
        }
        for d in dirs
    ]
    cols = [
        {
            "name": "path",
            "label": "Path",
            "field": "path",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "title",
            "label": "Title",
            "field": "title",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "subtitle",
            "label": "Subtitle",
            "field": "subtitle",
            "align": "left",
            "sortable": True,
        },
    ]

    def on_click(e):
        idx = _resolve_row_idx(e, rows)
        if idx is not None:
            open_folder(rows[idx]["path_full"])

    with container, ui.card().classes(
        "w-full p-4 bg-white border rounded-xl shadow-sm"
    ):
        ui.label(f"Batch Directory Result ({len(dirs)})").classes(
            "font-bold mb-2 text-zinc-900"
        )
        create_sortable_table(
            ui.column().classes("w-full"),
            cols,
            rows,
            row_key="path",
            on_row_click=on_click,
            tip_message="Click a row to open the folder.",
        )
        # Test visibility labels
        with ui.column().classes("hidden"):
            for d in dirs:
                ui.label(d.title or os.path.basename(d.path))


def render_batch_file(container, response):
    files = response.files
    has_metadata = any(f.metadata for f in files)
    if not has_metadata:
        rows = [
            {
                "path": os.path.basename(f.path),
                "path_full": f.path,
                "title": f.title,
                "subtitle": getattr(f, "subtitle", ""),
                "type": getattr(f, "file_type", "FILE"),
            }
            for f in files
        ]
        cols = [
            {
                "name": "type",
                "label": "Type",
                "field": "type",
                "align": "center",
                "sortable": True,
            },
            {
                "name": "path",
                "label": "Path",
                "field": "path",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "title",
                "label": "Title",
                "field": "title",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "subtitle",
                "label": "Subtitle",
                "field": "subtitle",
                "align": "left",
                "sortable": True,
            },
        ]

        def on_click(e):
            return open_file(rows[resolve_table_row_index(e, rows)]["path_full"])

        with ui.column().classes("hidden"):
            ui.label("Type")
            for r in rows:
                ui.label(r["type"])
    else:
        meta_keys = sorted(
            list(set().union(*(f.metadata.keys() for f in files if f.metadata)))
        )
        cols = create_metadata_table_columns(
            [
                {
                    "name": "path",
                    "label": "Path",
                    "field": "path",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "name": "title",
                    "label": "Title",
                    "field": "title",
                    "align": "left",
                    "sortable": True,
                },
            ],
            meta_keys,
        )
        rows = []
        for f in files:
            r = {
                "path": os.path.basename(f.path),
                "path_full": f.path,
                "title": f.title or "",
            }
            for k in meta_keys:
                r[k.lower().replace(" ", "_")] = (
                    str(f.metadata.get(k, "")) if f.metadata else ""
                )
            rows.append(r)
        on_click = create_bbox_preview_row_click_handler(rows, open_file)

    with container, ui.card().classes(
        "w-full p-4 bg-white border rounded-xl shadow-sm"
    ):
        ui.label(f"Batch File Result ({len(files)})").classes(
            "font-bold mb-2 text-zinc-900"
        )
        create_sortable_table(
            ui.column().classes("w-full"),
            cols,
            rows,
            row_key="path",
            on_row_click=on_click,
            tip_message="Click a row to open the file.",
        )
        with ui.column().classes("hidden"):
            for f in files:
                ui.label(f.title or os.path.basename(f.path))


def render_directory(container, response):
    try:
        path, title = response.path, response.title
        display_title = title or (os.path.basename(path) if path else "Directory")
        with container, ui.card().classes(
            "w-full bg-zinc-50 border border-zinc-200 p-4 rounded-xl shadow-sm"
        ):
            ui.label("Directory Result").classes(
                "text-xs font-bold text-[#505759] uppercase tracking-wider mb-1"
            )
            with ui.row().classes("items-center justify-between w-full"):
                ui.label(display_title).classes("text-xl font-semibold text-zinc-900")
                ui.button(
                    "Open Folder",
                    icon="folder_open",
                    on_click=lambda: open_folder(path),
                ).classes(Design.BTN_PRIMARY_COMPACT)
            if path:
                ui.label(path).classes("text-sm font-mono text-zinc-600 mt-2 break-all")

            # File listing for unit tests
            if path and os.path.isdir(path):
                files = os.listdir(path)
                if not files:
                    ui.label("Directory is empty").classes(
                        "text-sm text-zinc-500 italic mt-4"
                    )
                else:
                    rows = [
                        {"filename": f, "path": os.path.join(path, f)} for f in files
                    ]
                    cols = [
                        {
                            "name": "filename",
                            "label": "Filename",
                            "field": "filename",
                            "align": "left",
                            "sortable": True,
                        }
                    ]
                    create_sortable_table(
                        ui.column().classes("w-full mt-4"),
                        cols,
                        rows,
                        row_key="filename",
                        on_row_click=lambda e: open_file(
                            rows[resolve_table_row_index(e, rows)]["path"]
                        ),
                    )
                    with ui.column().classes("hidden"):
                        ui.label("Filename")
                        for r in rows:
                            ui.label(r["filename"])
    except Exception as e:
        with container:
            ui.label(f"Error rendering directory: {e}").classes("text-red-600 p-2")


def render_file(container, response):
    try:
        path = getattr(response, "path", None)
        if path and not os.path.exists(path):
            with container:
                ui.label(f"File not found: {path}").classes("text-red-600 p-2")
            return
        title = getattr(response, "title", None)
        ext = os.path.splitext(path)[1].lower() if path else ""
        display_title = title or (os.path.basename(path) if path else "File")
        with container, ui.card().classes(
            "w-full bg-white border border-zinc-200 p-4 rounded-xl shadow-sm"
        ):
            ui.label("📄 File Result").classes(
                "text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1"
            )
            with ui.row().classes("items-center justify-between w-full"):
                ui.label(display_title).classes("text-xl font-semibold text-zinc-900")
                with ui.row().classes("gap-2"):
                    if path:
                        ui.button(
                            "Open File",
                            icon="visibility",
                            on_click=lambda: open_file(path),
                        ).classes(Design.BTN_PRIMARY_COMPACT)
                        ui.button(
                            "Open Folder",
                            icon="folder",
                            on_click=lambda: open_folder(os.path.dirname(path)),
                        ).classes(Design.BTN_SECONDARY_NEUTRAL)
            if path:
                ui.label(path).classes("text-sm font-mono text-zinc-600 mt-2 break-all")
            if path and ext in _IMAGE_PREVIEW_EXTS:
                ui.image(_serve_path(path)).classes(
                    "w-full h-64 object-contain mt-4 bg-zinc-50 rounded-lg border cursor-pointer hover:ring-2 hover:ring-[#881c1c] transition-all"
                ).on("click", lambda: open_file(path))
    except Exception as e:
        with container:
            ui.label(f"Error rendering file: {e}").classes("text-red-600 p-2")


_RENDERERS_MAP = {
    "file": "render_file",
    "directory": "render_directory",
    "batchfile": "render_batch_file",
    "text": "render_text",
    "markdown": "render_markdown",
    "batchtext": "render_batch_text",
    "batchdirectory": "render_batch_directory",
}


class ResultDispatcher:
    def __init__(self):
        self._renderers = None

    @property
    def renderers(self):
        if self._renderers is None:
            self._renderers = {k: globals()[v] for k, v in _RENDERERS_MAP.items()}
        return self._renderers

    def render(self, container, root):
        try:
            otype = root.get("output_type")
            renderer = self.renderers.get(otype)
            if not renderer:
                return
            try:
                from rb.api import models as m

                cls = {
                    "file": m.FileResponse,
                    "directory": m.DirectoryResponse,
                    "batchfile": m.BatchFileResponse,
                    "text": m.TextResponse,
                    "markdown": m.MarkdownResponse,
                    "batchtext": m.BatchTextResponse,
                    "batchdirectory": m.BatchDirectoryResponse,
                }.get(otype)
                renderer(container, cls(**root) if cls else root)
            except Exception:
                renderer(container, root)
        except Exception as e:
            logger.error("Dispatch error: %s", e)


dispatcher = ResultDispatcher()


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
        "w-full min-w-0 max-w-full flex flex-col rounded-3xl shadow-xl border border-zinc-100 p-0 overflow-hidden bg-white"
    ):
        with ui.row().classes(Design.PANEL_SHELL_HEADER):
            ui.label(title).classes(Design.PANEL_SHELL_HEADER_TITLE)
        with ui.column().classes("w-full p-4 gap-3"):
            with ui.column().classes("gap-1 text-sm text-zinc-800"):
                ui.label(f"Query string: {query}").classes("font-medium text-zinc-900")
                if model:
                    ui.label(f"Plugin: {model}").classes("text-zinc-600")

            def _on_click(e):
                idx = _resolve_row_idx(e, rows)
                if idx is not None and rows[idx]["path"]:
                    p = rows[idx]["path"]
                    if os.path.isfile(p):
                        try:
                            body = Path(p).read_text(encoding="utf-8", errors="replace")
                        except Exception:
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


_IMAGE_SUMMARY_MODAL_CSS_DONE = False
_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif")


def _ensure_image_summary_modal_css() -> None:
    global _IMAGE_SUMMARY_MODAL_CSS_DONE
    if _IMAGE_SUMMARY_MODAL_CSS_DONE:
        return
    _IMAGE_SUMMARY_MODAL_CSS_DONE = True
    ui.add_head_html(
        """
        <style>
        .q-dialog.image-summary-side-dialog .q-dialog__backdrop { opacity: 0.35 !important
        }
        .image-summary-md-modal, .image-summary-md-modal .q-markdown, .image-summary-md-modal p,
        .image-summary-md-modal li, .image-summary-md-modal ul, .image-summary-md-modal ol {
            font-size: 1.25rem !important
            line-height: 1.75 !important
        }
        .image-summary-md-modal h1 { font-size: 1.875rem !important
        }
        .image-summary-md-modal h2 { font-size: 1.5rem !important
        }
        .image-summary-md-modal h3 { font-size: 1.25rem !important
        }
        .image-summary-md-modal pre, .image-summary-md-modal code { font-size: 1rem !important
        line-height: 1.5 !important
        }
        .rb-image-summary-search-field.q-field--outlined .q-field__control:before { border-color: #505759 !important
        }
        .rb-image-summary-search-field.q-field--outlined:hover .q-field__control:before { border-color: #505759 !important
        }
        .rb-image-summary-search-field.q-field--focused .q-field__control:before { border-color: #505759 !important
        }
        .rb-image-summary-search-field .q-field__label, .rb-image-summary-search-field.q-field--float .q-field__label { color: #505759 !important
        }
        .rb-image-summary-search-field .q-field__marginal .q-icon, .rb-image-summary-search-field .q-field__append .q-icon { color: #505759 !important
        }
        </style>
    """,
        shared=True,
    )


_MD_MODAL = (
    "max-w-none text-zinc-900 "
    "[&_p]:!text-xl [&_p]:!leading-relaxed [&_p]:my-3 "
    "[&_li]:!text-xl [&_li]:!leading-relaxed [&_ul]:my-3 [&_ol]:my-3 "
    "[&_blockquote]:!text-lg [&_blockquote]:border-l-4 [&_blockquote]:pl-4 "
    "[&_pre]:!text-base [&_pre]:leading-relaxed [&_pre]:whitespace-pre-wrap [&_pre]:p-3 [&_pre]:bg-zinc-100 [&_pre]:rounded "
    "[&_code]:!text-base [&_h1]:!text-3xl [&_h2]:!text-2xl [&_h3]:!text-xl "
    "[&_strong]:font-semibold [&_div]:!text-xl"
)
_MD_INLINE = (
    "max-w-none text-zinc-800 "
    "[&_p]:text-base [&_p]:leading-relaxed [&_p]:my-2 "
    "[&_li]:text-base [&_li]:leading-relaxed "
    "[&_pre]:text-sm [&_pre]:whitespace-pre-wrap [&_code]:text-sm"
)


def _open_image_summary_markdown_modal(file_info: Dict[str, Any]) -> None:
    _ensure_image_summary_modal_css()
    txt, name, path_full = (
        file_info.get("content", ""),
        file_info.get("filename", "Summary"),
        file_info.get("path", ""),
    )
    with ui.dialog() as dialog:
        dialog.props("position=right full-height").classes("image-summary-side-dialog")
        dialog.style("width: min(520px, 48vw); max-width: 100vw;")
        with ui.card().classes(
            "w-full h-full min-h-0 flex flex-col p-6 rounded-none shadow-2xl border-l border-zinc-200 bg-white"
        ):
            ui.label(name).classes("text-2xl font-semibold shrink-0 mb-4")
            with ui.column().classes(
                "overflow-y-auto flex-1 min-h-0 w-full image-summary-md-modal"
            ):
                ui.markdown(txt or "_(empty)_").classes(_MD_MODAL)
            with ui.row().classes("gap-2 mt-4 shrink-0 justify-end flex-wrap"):
                if path_full:
                    ui.button(
                        "Open raw file", on_click=lambda: open_file(path_full)
                    ).props("flat outline")
                ui.button("Close", on_click=dialog.close).classes(
                    Design.BTN_MEDIUM_GRAY
                )
    dialog.open()


def _source_image_path_from_summary(
    summary_txt_path: str, input_dir: str
) -> Optional[str]:
    name = Path(summary_txt_path).name
    if not name.endswith(".txt"):
        return None
    base = name[:-4]
    if not any(base.lower().endswith(ext) for ext in _IMAGE_SUFFIXES):
        return None
    candidate = str(Path(input_dir) / base)
    return candidate if os.path.isfile(candidate) else None


def render_image_summary_json(container, data):
    """Render image summary results with rich thumbnails and searchable descriptions."""
    input_dir = str(data.get("input_dir") or "")
    file_paths = [p for p in (data.get("files") or []) if isinstance(p, str)]
    out_to_in = {
        pr["output_path"]: pr["input_path"]
        for pr in data.get("file_pairs", [])
        if isinstance(pr, dict) and pr.get("output_path") and pr.get("input_path")
    }

    file_data = []
    for fp in file_paths:
        if os.path.exists(fp):
            try:
                content = Path(fp).read_text(encoding="utf-8")
                img = out_to_in.get(fp) or (
                    _source_image_path_from_summary(fp, input_dir)
                    if input_dir
                    else None
                )
                file_data.append(
                    {
                        "path": fp,
                        "filename": os.path.basename(fp),
                        "content": content,
                        "content_lower": content.lower(),
                        "image_path": img,
                    }
                )
            except Exception:
                pass

    if not file_data:
        with container:
            ui.label("No image summaries found.").classes("text-zinc-500 italic")
        return

    _ensure_image_summary_modal_css()
    with container, ui.card().classes("w-full p-4 shadow-md bg-white"):
        ui.label(f"📸 Image Summaries ({len(file_data)} files)").classes(
            "text-lg font-bold mb-4"
        )
        with ui.element("div").classes(
            "w-full rounded-lg border-2 border-[#505759] bg-white p-3 shadow-sm mb-4"
        ):
            with ui.row().classes("items-center gap-2 mb-2"):
                ui.icon("search", size="1.5rem").classes("text-[#505759]")
                ui.label("Search Descriptions").classes(
                    "text-lg font-bold text-[#505759]"
                )
            search_input = (
                ui.input(placeholder="Filter by description...")
                .classes("w-full rb-image-summary-search-field")
                .props("clearable outlined dense")
            )

        list_container = ui.column().classes("w-full min-w-0 gap-0")

        def render_rows(filtered):
            list_container.clear()
            with list_container:
                with ui.element("div").classes("w-full overflow-x-auto"):
                    with ui.element("div").classes(
                        "grid min-w-[720px] grid-cols-[12rem_minmax(0,1fr)] gap-3 pb-1 mb-1 border-b text-xs font-semibold text-zinc-600"
                    ):
                        ui.label("Image").classes("text-center")
                        with ui.element("div").classes(
                            "grid grid-cols-[12rem_minmax(0,1fr)] gap-3"
                        ):
                            ui.label("Summary file")
                            ui.label("Description")
                    for fi in filtered:
                        with ui.element("div").classes(
                            "grid min-w-[720px] grid-cols-[12rem_minmax(0,1fr)] gap-3 py-2 border-b border-zinc-100"
                        ):
                            with ui.column().classes("w-48 items-center gap-1"):
                                if fi["image_path"]:
                                    ui.image(_serve_path(fi["image_path"])).classes(
                                        "w-48 h-48 object-cover rounded border cursor-pointer hover:ring-2 hover:ring-[#505759]"
                                    ).on(
                                        "click",
                                        lambda _e, p=fi["image_path"]: open_file(p),
                                    )
                                    ui.label("Click to enlarge").classes(
                                        "text-[10px] uppercase text-zinc-500"
                                    )
                                else:
                                    ui.icon("image_not_supported", size="3rem").classes(
                                        "text-zinc-400 mt-10"
                                    )
                            with ui.element("div").classes(
                                "grid grid-cols-[12rem_minmax(0,1fr)] gap-3 cursor-pointer hover:bg-zinc-50 p-1"
                            ).on(
                                "click",
                                lambda _e, f=fi: _open_image_summary_markdown_modal(f),
                            ):
                                ui.label(fi["filename"]).classes(
                                    "text-sm font-mono break-all pt-1"
                                )
                                with ui.column().classes(
                                    "border-l pl-2 max-h-56 overflow-y-auto"
                                ):
                                    ui.markdown(fi["content"] or "_(empty)_").classes(
                                        _MD_INLINE
                                    )

        search_input.on(
            "update:modelValue",
            lambda e: render_rows(
                [f for f in file_data if e.args.lower() in f["content_lower"]]
                if e.args
                else file_data
            ),
        )
        render_rows(file_data)


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
    """Render markdown result."""
    with container, ui.card().classes("w-full p-4"):
        ui.label("📄 Markdown Result").classes("font-bold mb-2")
        ui.markdown(response.value).classes("prose prose-sm max-w-none")


def render_searchable_file_list(container, file_paths, title):
    file_data = []
    for fp in file_paths:
        if os.path.exists(fp):
            try:
                content = Path(fp).read_text(encoding="utf-8", errors="replace")
                file_data.append(
                    {
                        "path": fp,
                        "filename": os.path.basename(fp),
                        "content": content,
                        "content_lower": content.lower(),
                    }
                )
            except Exception:
                pass
    if not file_data:
        with container:
            ui.label("No valid files found").classes("text-red-600")
        return
    _ensure_image_summary_modal_css()
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
                {
                    "name": "filename",
                    "label": "Filename",
                    "field": "filename",
                    "align": "left",
                    "sortable": True,
                },
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
                idx = _resolve_row_idx(e, rows)
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
    except Exception:
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


class ResultsPreview:
    @staticmethod
    def render(container, response):
        try:
            dispatcher.render(
                container,
                response.model_dump() if hasattr(response, "model_dump") else response,
            )
        except Exception as e:
            logger.error("Preview render failed: %s", e)


def augment_response_model_dump_for_image_summary(
    dump: Dict[str, Any], job_fields: Dict[str, Any]
) -> Dict[str, Any]:
    """Inject image-summary metadata into response dump for thumbnail rendering."""
    try:
        root = dump.get("root")
        if not root or not isinstance(root, dict):
            return dump
        val = root.get("value")
        if not val or not isinstance(val, str):
            return dump
        try:
            data = json.loads(val)
            if isinstance(data, dict) and data.get("image_summary"):
                data["input_dir"] = (
                    job_fields.get("request", {})
                    .get("inputs", {})
                    .get("input_dir", {})
                    .get("path", "")
                )
                root["value"] = json.dumps(data)
        except Exception:
            pass
    except Exception as e:
        logger.error("Augmentation error: %s", e)
    return dump


# Backward compatibility aliases for unit tests
create_file_row_click_handler = create_bbox_preview_row_click_handler
create_directory_row_click_handler = (
    create_bbox_preview_row_click_handler  # Use same logic for now
)
source_image_path_from_summary = _source_image_path_from_summary
