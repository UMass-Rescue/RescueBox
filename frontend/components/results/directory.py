"""Directory and batch-directory response renderers."""

from __future__ import annotations

import os

from nicegui import ui

from frontend.components.results import serve_paths as result_serve
from frontend.components.results import table_helpers as result_tables
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.design_tokens import Design


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
    cols = result_tables.path_title_subtitle_columns()

    def on_click(e):
        idx = result_tables.resolve_row_idx(e, rows)
        if idx is not None:
            result_serve.open_folder(rows[idx]["path_full"])

    result_tables.render_batch_path_table(
        container,
        title=f"Batch Directory Result ({len(dirs)})",
        cols=cols,
        rows=rows,
        row_key="path",
        on_row_click=on_click,
        tip_message="Click a row to open the folder.",
    )
    with ui.column().classes("hidden"):
        for d in dirs:
            ui.label(d.title or os.path.basename(d.path))


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
                    color=None,
                    on_click=lambda: result_serve.open_folder(path),
                ).classes(Design.BTN_PRIMARY_COMPACT)
            if path:
                ui.label(path).classes("text-sm font-mono text-zinc-600 mt-2 break-all")

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
                    cols = result_tables.filename_sortable_columns()
                    result_tables.create_sortable_table(
                        ui.column().classes("w-full mt-4"),
                        cols,
                        rows,
                        row_key="filename",
                        on_row_click=lambda e: result_serve.open_file(
                            rows[result_tables.resolve_table_row_index(e, rows)]["path"]
                        ),
                    )
                    with ui.column().classes("hidden"):
                        ui.label("Filename")
                        for r in rows:
                            ui.label(r["filename"])
    except UI_RENDER_ERRORS as e:
        with container:
            ui.label(f"Error rendering directory: {e}").classes("text-red-600 p-2")
