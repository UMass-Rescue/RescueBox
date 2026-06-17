"""Image-summary JSON payloads embedded in text responses."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from nicegui import ui

from .table_helpers import file_search_result_row
from .serve_paths import open_file, serve_path
from frontend.design_tokens import Design
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.database.pipeline_lineage_utils import source_image_path_from_summary

_IMAGE_SUMMARY_MODAL_CSS_DONE = False  # kept for test patches referencing module state

_MD_MODAL = (
    "max-w-none text-zinc-900 "
    "[&_p]:!text-xl [&_p]:!leading-relaxed [&_p]:my-3 "
    "[&_li]:!text-xl [&_li]:!leading-relaxed [&_ul]:my-3 [&_ol]:my-3 "
    "[&_blockquote]:!text-lg [&_blockquote]:border-l-4 [&_blockquote]:pl-4 "
    "[&_pre]:!text-base [&_pre]:leading-relaxed [&_pre]:whitespace-pre-wrap "
    "[&_pre]:p-3 [&_pre]:bg-zinc-100 [&_pre]:rounded "
    "[&_code]:!text-base [&_h1]:!text-3xl [&_h2]:!text-2xl [&_h3]:!text-xl "
    "[&_strong]:font-semibold [&_div]:!text-xl"
)
_MD_INLINE = (
    "max-w-none text-zinc-800 "
    "[&_p]:text-base [&_p]:leading-relaxed [&_p]:my-2 "
    "[&_li]:text-base [&_li]:leading-relaxed "
    "[&_pre]:text-sm [&_pre]:whitespace-pre-wrap [&_code]:text-sm"
)


class _ImageSummaryCssState:
    done = False

    @classmethod
    def mark_done(cls) -> None:
        cls.done = True

    @classmethod
    def is_done(cls) -> bool:
        return cls.done


def ensure_image_summary_modal_css() -> None:
    if _ImageSummaryCssState.is_done():
        return
    _ImageSummaryCssState.mark_done()
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
        .rb-image-summary-search-field.q-field--outlined .q-field__control:before {
            border-color: #505759 !important
        }
        .rb-image-summary-search-field.q-field--outlined:hover .q-field__control:before {
            border-color: #505759 !important
        }
        .rb-image-summary-search-field.q-field--focused .q-field__control:before {
            border-color: #505759 !important
        }
        .rb-image-summary-search-field .q-field__label,
        .rb-image-summary-search-field.q-field--float .q-field__label {
            color: #505759 !important
        }
        .rb-image-summary-search-field .q-field__marginal .q-icon,
        .rb-image-summary-search-field .q-field__append .q-icon {
            color: #505759 !important
        }
        </style>
    """,
        shared=True,
    )


def _open_image_summary_markdown_modal(file_info: Dict[str, Any]) -> None:
    ensure_image_summary_modal_css()
    txt, name, path_full = (
        file_info.get("content", ""),
        file_info.get("filename", "Summary"),
        file_info.get("path", ""),
    )
    with ui.dialog() as dialog:
        dialog.props("position=right full-height").classes("image-summary-side-dialog")
        with ui.card().classes(
            "h-full min-h-0 flex flex-col p-6 rounded-none shadow-2xl border-l border-zinc-200 bg-white"
        ).style("width: min(520px, 48vw); max-width: 100vw;"):
            ui.label(name).classes("text-2xl font-semibold shrink-0 mb-4")
            with ui.column().classes(
                "overflow-y-auto flex-1 min-h-0 w-full image-summary-md-modal"
            ):
                ui.markdown(txt or "_(empty)_").classes(_MD_MODAL)
            with ui.row().classes("gap-2 mt-4 shrink-0 justify-end flex-wrap"):
                if path_full:
                    ui.button(
                        "Open raw file",
                        color=None,
                        on_click=lambda: open_file(path_full),
                    ).classes(Design.BTN_SECONDARY_NEUTRAL)

                    def _download_raw():
                        try:
                            with open(path_full, "rb") as f:
                                data = f.read()
                            ui.download(data, os.path.basename(path_full))
                        except UI_RENDER_ERRORS as e:
                            ui.notify(f"Error downloading file: {e}", type="negative")

                    ui.button(
                        "Download raw file", color=None, on_click=_download_raw
                    ).classes(Design.BTN_SECONDARY_NEUTRAL)

                ui.button("Close", color=None, on_click=dialog.close).classes(
                    Design.BTN_MEDIUM_GRAY
                )
    dialog.open()


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
                    source_image_path_from_summary(fp, input_dir) if input_dir else None
                )
                file_data.append(file_search_result_row(fp, content, image_path=img))
            except UI_RENDER_ERRORS:
                pass

    if not file_data:
        with container:
            ui.label("No image summaries found.").classes("text-zinc-500 italic")
        return

    ensure_image_summary_modal_css()
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
                    grid_head_cls = (
                        "grid min-w-[720px] grid-cols-[12rem_minmax(0,1fr)] gap-3 "
                        "pb-1 mb-1 border-b text-xs font-semibold text-zinc-600"
                    )
                    with ui.element("div").classes(grid_head_cls):
                        ui.label("Image").classes("text-center")
                        with ui.element("div").classes(
                            "grid grid-cols-[12rem_minmax(0,1fr)] gap-3"
                        ):
                            ui.label("Summary file")
                            ui.label("Description")
                    grid_row_cls = (
                        "grid min-w-[720px] grid-cols-[12rem_minmax(0,1fr)] gap-3 "
                        "py-2 border-b border-zinc-100"
                    )
                    for fi in filtered:
                        with ui.element("div").classes(grid_row_cls):
                            with ui.column().classes("w-48 items-center gap-1"):
                                if fi["image_path"]:
                                    ui.image(serve_path(fi["image_path"])).classes(
                                        "w-48 h-48 object-cover rounded border "
                                        "cursor-pointer hover:ring-2 hover:ring-[#505759]"
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
