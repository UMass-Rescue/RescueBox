"""File and batch-file response renderers."""

from __future__ import annotations

import os

from nicegui import ui

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.design_tokens import Design

from .serve_paths import (
    IMAGE_PREVIEW_EXTS,
    open_file,
    open_folder,
    serve_path,
)
from .table_helpers import (
    JSON_VIEW_LABEL,
    create_bbox_preview_row_click_handler,
    create_metadata_table_columns,
    create_sortable_table,
    display_filename,
    enrich_row_with_thumbnail,
    is_image_result_row,
    json_storage_key,
    looks_like_json_object,
    metadata_field_key,
    path_title_subtitle_columns,
    resolve_table_row_index,
    thumbnail_table_column,
)


def _files_support_preview_toggle(files) -> bool:
    return any(
        is_image_result_row(
            f.path,
            file_type=getattr(f, "file_type", None),
            metadata=getattr(f, "metadata", None),
        )
        for f in files
    )


def _batch_file_row(f, *, preview_on: bool, extra: dict | None = None) -> dict:
    row = {
        "path": display_filename(f.path),
        "path_full": f.path,
        **(extra or {}),
    }
    if not preview_on:
        return row
    return enrich_row_with_thumbnail(
        row,
        file_type=getattr(f, "file_type", None),
        metadata=getattr(f, "metadata", None),
    )


def _prepend_thumbnail_column(cols: list[dict], rows: list[dict]) -> list[dict]:
    if any(row.get("thumbnail_url") or row.get("preview_unavailable") for row in rows):
        return [thumbnail_table_column(), *cols]
    return cols


_PREVIEW_HELP = "Shows thumbnails for only local match images"


def _switch_is_on(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


def _batch_tip_message(preview_on: bool) -> str:
    if preview_on:
        return (
            "Local matches show a thumbnail in Preview — click it or the row to "
            "open the full image."
        )
    return "Click a row to open the file."


def _fill_metadata_row(r: dict, f, meta_keys: list[str]) -> dict:
    for k in meta_keys:
        field = metadata_field_key(k)
        raw = f.metadata.get(k, "") if f.metadata else ""
        if looks_like_json_object(raw):
            r[json_storage_key(field)] = raw
            r[field] = JSON_VIEW_LABEL
        else:
            r[field] = str(raw) if raw is not None else ""
    return r


def render_batch_file(container, response):
    files = response.files
    has_metadata = any(f.metadata for f in files)
    preview_toggle = _files_support_preview_toggle(files)
    if not has_metadata:
        base_cols = [
            {
                "name": "type",
                "label": "Type",
                "field": "type",
                "align": "center",
                "sortable": True,
            },
            *path_title_subtitle_columns(path_label="Filename"),
        ]
        meta_keys: list[str] = []
    else:
        meta_keys = sorted(
            list(set().union(*(f.metadata.keys() for f in files if f.metadata)))
        )
        base_cols = create_metadata_table_columns(
            path_title_subtitle_columns(path_label="Filename")[:2],
            meta_keys,
        )

    def build_rows(preview_on: bool) -> list[dict]:
        rows = []
        for f in files:
            extra = (
                {"title": f.title or ""}
                if has_metadata
                else {
                    "title": f.title,
                    "subtitle": getattr(f, "subtitle", ""),
                    "type": getattr(f, "file_type", "FILE"),
                }
            )
            row = _batch_file_row(f, preview_on=preview_on, extra=extra)
            if has_metadata:
                row = _fill_metadata_row(row, f, meta_keys)
            rows.append(row)
        return rows

    def build_cols(preview_on: bool, rows: list[dict]) -> list[dict]:
        cols = list(base_cols)
        if preview_on:
            cols = _prepend_thumbnail_column(cols, rows)
        return cols

    def build_on_click(rows: list[dict]):
        if has_metadata:
            return create_bbox_preview_row_click_handler(rows, open_file)

        def on_click(e):
            idx = resolve_table_row_index(e, rows)
            if idx is not None:
                open_file(rows[idx]["path_full"])

        return on_click

    title = f"Batch File Result ({len(files)})"
    with container, ui.card().classes(
        "w-full p-4 bg-white border rounded-xl shadow-sm"
    ):
        preview_switch = None
        with ui.row().classes(
            "items-start justify-between w-full gap-4 mb-2 flex-wrap"
        ):
            ui.label(title).classes("font-bold text-zinc-900")
            if preview_toggle:
                with ui.column().classes("items-end gap-1 max-w-md"):
                    preview_switch = ui.switch(
                        "Show match image previews",
                        value=False,
                    ).props("dense").classes("text-sm text-zinc-800")
                    ui.label(_PREVIEW_HELP).classes(
                        "text-sm text-zinc-600 text-right leading-relaxed"
                    )

        table_host = ui.column().classes("w-full")
        tip_label = ui.label("").classes("text-xs text-zinc-500 mt-2")

        def render_table(preview_on: bool) -> None:
            table_host.clear()
            rows = build_rows(preview_on)
            cols = build_cols(preview_on, rows)
            tip_label.set_text(f"💡 {_batch_tip_message(preview_on)}")
            create_sortable_table(
                table_host,
                cols,
                rows,
                row_key="filename",
                on_row_click=build_on_click(rows),
            )

        if preview_switch is not None:
            def on_preview_toggle(_e) -> None:
                render_table(_switch_is_on(preview_switch.value))

            preview_switch.on("update:modelValue", on_preview_toggle)
        render_table(False)

    with ui.column().classes("hidden"):
        if not has_metadata:
            ui.label("Type")
        for f in files:
            ui.label(f.title or os.path.basename(f.path))


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
            ui.label("File Result").classes(
                "text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1"
            )
            with ui.row().classes("items-center justify-between w-full"):
                ui.label(display_title).classes("text-xl font-semibold text-zinc-900")
                with ui.row().classes("gap-2"):
                    if path:
                        ui.button(
                            "Open File",
                            color=None,
                            on_click=lambda: open_file(path),
                        ).classes(Design.BTN_PRIMARY_COMPACT)

                        def _download_file(file_path=path):
                            try:
                                with open(file_path, "rb") as f:
                                    ui.download(f.read(), os.path.basename(file_path))
                            except UI_RENDER_ERRORS as e:
                                ui.notify(
                                    f"Error downloading file: {e}", type="negative"
                                )

                        ui.button(
                            "Download",
                            color=None,
                            on_click=_download_file,
                        ).classes(Design.BTN_SECONDARY_NEUTRAL)
                        ui.button(
                            "Open Folder",
                            color=None,
                            on_click=lambda: open_folder(os.path.dirname(path)),
                        ).classes(Design.BTN_SECONDARY_NEUTRAL)
            if path:
                ui.label(path).classes("text-sm font-mono text-zinc-600 mt-2 break-all")
            if path and ext in IMAGE_PREVIEW_EXTS:
                ui.image(serve_path(path)).classes(
                    "w-full h-64 object-contain mt-4 bg-zinc-50 rounded-lg border "
                    "cursor-pointer hover:ring-2 hover:ring-[#881c1c] transition-all"
                ).on("click", lambda: open_file(path))
    except UI_RENDER_ERRORS as e:
        with container:
            ui.label(f"Error rendering file: {e}").classes("text-red-600 p-2")
