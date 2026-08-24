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
    create_bbox_preview_row_click_handler,
    create_metadata_table_columns,
    path_title_subtitle_columns,
    render_batch_path_table,
    resolve_table_row_index,
)


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
            *path_title_subtitle_columns(),
        ]

        def on_click(e):
            idx = resolve_table_row_index(e, rows)
            if idx is not None:
                open_file(rows[idx]["path_full"])

        with ui.column().classes("hidden"):
            ui.label("Type")
            for r in rows:
                ui.label(r["type"])
    else:
        meta_keys = sorted(
            list(set().union(*(f.metadata.keys() for f in files if f.metadata)))
        )
        cols = create_metadata_table_columns(
            path_title_subtitle_columns()[:2],
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

    render_batch_path_table(
        container,
        title=f"Batch File Result ({len(files)})",
        cols=cols,
        rows=rows,
        row_key="filename",
        on_row_click=on_click,
        tip_message="Click a row to open the file.",
    )
    with ui.column().classes("hidden"):
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
