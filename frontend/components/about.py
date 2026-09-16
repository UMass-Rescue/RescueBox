from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import unquote

from nicegui import ui
from starlette.requests import Request

from frontend.components.demo import (
    render_guided_markdown_body,
    strip_editor_comment,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LICENSE_ROOT = _REPO_ROOT / "License&Copyright"
# Relative to LICENSE_ROOT — default document when ``?doc=`` is missing/invalid.
DEFAULT_LICENSE_REL = "LICENSE"

# Top-level RescueBox notices (label shown in UI → path under LICENSE_ROOT).
_PRIMARY_DOC_ENTRIES: tuple[tuple[str, str], ...] = (
    ("LICENSE", "LICENSE"),
    ("COPYRIGHT", "COPYRIGHT.txt"),
    ("NOTICE", "NOTICE"),
)
_THIRD_PARTY_SENTINEL = "Third_Party Licenses"

_MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})


def _safe_relative_file(root: Path, rel: str) -> Path | None:
    if not rel or rel.strip() != rel:
        return None
    if ".." in rel or rel.startswith(("/", "\\")):
        return None
    try:
        candidate = (root / rel).resolve()
        candidate.relative_to(root.resolve())
    except (ValueError, OSError, RuntimeError):
        return None
    if not candidate.is_file():
        return None
    return candidate


def list_text_docs(root: Path) -> list[str]:
    """Sorted relative POSIX paths for readable license-style files."""
    if not root.is_dir():
        return []
    out: list[str] = []
    try:
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            suf = p.suffix.lower()
            name = p.name
            if suf in _MARKDOWN_SUFFIXES or suf == ".txt":
                out.append(p.relative_to(root).as_posix())
                continue
            if not suf and name.upper() in {"LICENSE", "NOTICE", "COPYRIGHT"}:
                out.append(p.relative_to(root).as_posix())
    except OSError as e:
        logger.warning("Cannot list license tree %s: %s", root, e)
        return []
    return sorted(out, key=str.lower)


def _primary_and_third_party_paths(
    files: list[str],
) -> tuple[list[tuple[str, str]], list[str]]:
    """Split listing into top-level LICENSE/COPYRIGHT/NOTICE vs nested third-party files."""
    present = set(files)
    primary: list[tuple[str, str]] = []
    primary_paths: set[str] = set()
    for label, relpath in _PRIMARY_DOC_ENTRIES:
        if relpath in present:
            primary.append((label, relpath))
            primary_paths.add(relpath)
    third_party = sorted(
        (f for f in files if f not in primary_paths),
        key=str.lower,
    )
    return primary, third_party


def render_one_file(
    container: ui.element, root: Path, rel: str, *, static_url: str
) -> None:
    path = _safe_relative_file(root, rel)
    if path is None:
        ui.label("Could not open that document.").classes("text-red-600")
        return
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.warning("Read failed %s: %s", path, e)
        ui.label(f"Could not read file: {e}").classes("text-red-600")
        return
    base = static_url.rstrip("/")
    if path.suffix.lower() in _MARKDOWN_SUFFIXES:
        render_guided_markdown_body(
            container,
            strip_editor_comment(raw),
            image_base_url=base,
        )
    else:
        with container:
            ui.label(path.relative_to(root).as_posix()).classes(
                "text-sm text-zinc-500 font-mono mb-2"
            )
            ui.code(raw).classes(
                "w-full max-w-none text-sm whitespace-pre-wrap break-words "
                "block p-4 bg-slate-50 rounded-xl border border-slate-200 shadow-inner"
            )


def render_license_documents_section(
    request: Request,
    *,
    static_url: str = "/license-copyright",
    page_path: str = "/about",
) -> None:
    """License & Copyright picker and viewer; uses dynamic, inline, closable, and scrollable rendering."""
    root = LICENSE_ROOT
    files = list_text_docs(root)

    ui.element("div").props(
        f'id="license-copyright" data-page-path="{page_path}"'
    ).classes("scroll-mt-24")
    with ui.card().classes(
        "w-full max-w-3xl p-6 bg-white border border-slate-200 rounded-2xl shadow-md "
        "border-t-4 border-t-[#881c1c] flex flex-col gap-4"
    ):
        ui.label("License & Copyright").classes("text-xl font-semibold text-slate-800")
        ui.label(
            "Select a document below to view RescueBox LICENSE, COPYRIGHT, NOTICE, or bundled third-party notices."
        ).classes("text-sm text-zinc-600")

        if not root.is_dir():
            ui.label(f"Folder not found: {root}").classes("text-red-600")
            return
        if not files:
            ui.label("No license documents found in that folder.").classes(
                "text-zinc-600"
            )
            return

        primary_entries, third_party_files = _primary_and_third_party_paths(files)

        # Main options for the select dropdown
        main_options: dict[str, str] = {path: label for label, path in primary_entries}
        if third_party_files:
            main_options[_THIRD_PARTY_SENTINEL] = "Third party"

        # Dropdowns row (handlers defined below; lambdas defer binding)
        with ui.row().classes("w-full gap-4 items-center flex-wrap sm:flex-nowrap"):
            main_select = ui.select(
                options=main_options,
                label="Document",
                value=None,
            ).classes("flex-1 min-w-[200px]")

            third_select = ui.select(
                options=third_party_files,
                label="Third-party document",
                value=None,
            ).classes("flex-1 min-w-[200px]")
            third_select.visible = False

        with ui.card().classes(
            "w-full p-4 bg-slate-50 border border-slate-200 rounded-xl shadow-sm flex flex-col gap-3"
        ) as viewer_card:
            viewer_card.visible = False

            with ui.row().classes(
                "w-full justify-between items-center border-b pb-2 border-slate-200"
            ):
                with ui.row().classes("items-center gap-2"):
                    viewer_title = ui.label("").classes(
                        "text-sm font-bold text-slate-700 font-mono"
                    )

                close_btn = (
                    ui.button(
                        "Close",
                        color=None,
                    )
                    .props("flat dense no-caps")
                    .classes(
                        "text-slate-600 hover:text-slate-800 hover:bg-slate-100 px-3 py-1 "
                        "rounded-lg border border-slate-200 transition-colors text-sm font-medium"
                    )
                )

            viewer_body = ui.column().classes(
                "w-full max-h-[350px] overflow-y-auto pr-2"
            )

        def _show_document(rel_path: str):
            viewer_body.clear()
            viewer_title.text = rel_path
            render_one_file(viewer_body, root, rel_path, static_url=static_url)
            viewer_card.visible = True

        def _close_viewer(_event=None):
            viewer_card.visible = False
            main_select.value = None
            third_select.value = None
            third_select.visible = False

        def _on_main_change(e):
            val = e.value
            if not val:
                return
            if val == _THIRD_PARTY_SENTINEL:
                third_select.visible = True
                first_third = third_party_files[0] if third_party_files else None
                if first_third:
                    third_select.value = first_third
                    _show_document(first_third)
            else:
                third_select.visible = False
                third_select.value = None
                _show_document(val)

        def _on_third_change(e):
            val = e.value
            if val and val in third_party_files:
                _show_document(val)

        # NiceGUI event API: prefer `on_value_change` (newer), fall back to `on_change` (older).
        if hasattr(main_select, "on_value_change"):
            main_select.on_value_change(_on_main_change)
        else:
            main_select.on_change(_on_main_change)

        if hasattr(third_select, "on_value_change"):
            third_select.on_value_change(_on_third_change)
        else:
            third_select.on_change(_on_third_change)
        close_btn.on_click(_close_viewer)

        # Initial load from query param if present
        doc = request.query_params.get("doc")
        if doc:
            rel = unquote(doc)
            if rel in files:
                if rel in third_party_files:
                    main_select.value = _THIRD_PARTY_SENTINEL
                    third_select.value = rel
                    third_select.visible = True
                else:
                    main_select.value = rel
                _show_document(rel)
