"""Shared table and bbox preview helpers for result renderers."""

from __future__ import annotations

import ast
import os

from nicegui import ui
from PIL import Image, ImageDraw

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.design_tokens import Design

from .serve_paths import open_file, open_folder

_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
_MAX_PREVIEW_SIDE = 1600


def create_metadata_table_columns(
    base_columns: list[dict], metadata_keys: list[str]
) -> list[dict]:
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


def resolve_table_row_index(e, rows: list[dict]) -> int | None:
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
    except UI_RENDER_ERRORS:
        pass
    return None


def resolve_row_idx(e, rows: list[dict]) -> int | None:
    return resolve_table_row_index(e, rows)


def parse_int_bbox(value: object) -> tuple[int, int, int, int] | None:
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
    source: Image.Image, bbox: tuple[int, int, int, int]
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
    abs_path: str, bbox: tuple[int, int, int, int], row: dict
) -> None:
    try:
        with Image.open(abs_path) as im0:
            im0.load()
            preview = _pil_image_with_bbox_drawn(im0.copy(), bbox)
    except UI_RENDER_ERRORS:
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
                color=None,
                on_click=lambda: open_folder(os.path.dirname(abs_path)),
            ).classes(Design.BTN_SECONDARY_NEUTRAL)
            ui.button("Close", color=None, on_click=dialog.close).classes(
                Design.BTN_MEDIUM_GRAY
            )
    dialog.open()


def create_bbox_preview_row_click_handler(rows: list[dict], open_file_func):
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


create_file_row_click_handler = create_bbox_preview_row_click_handler
create_directory_row_click_handler = create_bbox_preview_row_click_handler


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


def path_title_subtitle_columns() -> list[dict]:
    """Quasar table columns for path / title / subtitle rows."""
    return [
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


def filename_sortable_columns() -> list[dict]:
    return [
        {
            "name": "filename",
            "label": "Filename",
            "field": "filename",
            "align": "left",
            "sortable": True,
        }
    ]


def file_search_result_row(
    fp: str, content: str, *, image_path: str | None = None
) -> dict:
    row = {
        "path": fp,
        "filename": os.path.basename(fp),
        "content": content,
        "content_lower": content.lower(),
    }
    if image_path:
        row["image_path"] = image_path
    return row


def render_batch_path_table(
    container,
    *,
    title: str,
    cols: list[dict],
    rows: list[dict],
    row_key: str,
    on_row_click,
    tip_message: str,
) -> None:
    with container, ui.card().classes(
        "w-full p-4 bg-white border rounded-xl shadow-sm"
    ):
        ui.label(title).classes("font-bold mb-2 text-zinc-900")
        create_sortable_table(
            ui.column().classes("w-full"),
            cols,
            rows,
            row_key=row_key,
            on_row_click=on_row_click,
            tip_message=tip_message,
        )
