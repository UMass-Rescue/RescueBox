"""Load and render License&Copyright documents (shared by About and /licenses redirect)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import quote, unquote

from nicegui import ui
from starlette.requests import Request

from frontend.components.demo.guided_markdown import (
    render_guided_markdown_body,
    strip_editor_comment,
)

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LICENSE_ROOT = _REPO_ROOT / "License&Copyright"
# Relative to LICENSE_ROOT — default document when ``?doc=`` is missing/invalid.
DEFAULT_LICENSE_REL = "LICENSE"

# Top-level RescueBox notices (label shown in UI → path under LICENSE_ROOT).
_PRIMARY_DOC_ENTRIES: Tuple[Tuple[str, str], ...] = (
    ("LICENSE", "LICENSE"),
    ("COPYRIGHT", "COPYRIGHT.txt"),
    ("NOTICE", "NOTICE"),
)
_THIRD_PARTY_SENTINEL = "Third_Party Licenses"

_MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})


def _safe_relative_file(root: Path, rel: str) -> Optional[Path]:
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


def list_text_docs(root: Path) -> List[str]:
    """Sorted relative POSIX paths for readable license-style files."""
    if not root.is_dir():
        return []
    out: List[str] = []
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
    files: List[str],
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


def render_one_file(container: ui.element, root: Path, rel: str, *, static_url: str) -> None:
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
                "block p-4 bg-zinc-50 rounded border border-zinc-200"
            )


def render_license_documents_section(
    request: Request,
    *,
    static_url: str = "/license-copyright",
    page_path: str = "/about",
) -> None:
    """License & Copyright picker and viewer; uses ``?doc=`` on ``page_path``."""
    doc = request.query_params.get("doc")
    root = LICENSE_ROOT
    files = list_text_docs(root)

    ui.element("div").props('id="license-copyright"').classes("scroll-mt-24")
    ui.label("License & Copyright").classes("text-xl font-semibold mb-2")
    ui.label(
        "RescueBox LICENSE, COPYRIGHT, and NOTICE at the top; bundled third-party notices when you choose Third party."
    ).classes("text-sm text-zinc-600 mb-4")

    if not root.is_dir():
        ui.label(f"Folder not found: {root}").classes("text-red-600")
        return
    if not files:
        ui.label("No license documents found in that folder.").classes("text-zinc-600")
        return

    primary_entries, third_party_files = _primary_and_third_party_paths(files)

    rel = unquote(doc) if doc else ""
    if rel not in files:
        if DEFAULT_LICENSE_REL in files:
            rel = DEFAULT_LICENSE_REL
        elif primary_entries:
            rel = primary_entries[0][1]
        else:
            rel = files[0]

    base = page_path.rstrip("/") or "/about"

    def _navigate_to_doc(new_rel: str) -> None:
        if new_rel in files:
            ui.navigate.to(f"{base}?doc={quote(new_rel, safe='')}")

    # Main picker: primary docs + optional "Third party".
    # NiceGUI dict options are {value: label} (keys are selected values; values are shown in the UI).
    main_options: dict[str, str] = {path: label for label, path in primary_entries}
    if third_party_files:
        main_options[_THIRD_PARTY_SENTINEL] = "Third party"

    if rel in third_party_files:
        main_value = _THIRD_PARTY_SENTINEL
    else:
        main_value = next(
            (path for label, path in primary_entries if path == rel),
            primary_entries[0][1] if primary_entries else rel,
        )

    def _on_main_pick(e) -> None:
        v = e.value
        if not isinstance(v, str):
            return
        if v == _THIRD_PARTY_SENTINEL and third_party_files:
            target = (
                rel
                if rel in third_party_files
                else third_party_files[0]
            )
            _navigate_to_doc(target)
        elif v != _THIRD_PARTY_SENTINEL:
            _navigate_to_doc(v)

    ui.select(
        options=main_options,
        value=main_value,
        label="Document",
        on_change=_on_main_pick,
    ).classes("w-full max-w-2xl")

    if third_party_files:
        with ui.column().classes("w-full max-w-2xl mt-2") as third_wrap:
            third_wrap.visible = rel in third_party_files

            def _on_third_pick(e) -> None:
                v = e.value
                if isinstance(v, str) and v in third_party_files:
                    _navigate_to_doc(v)

            ui.select(
                options=third_party_files,
                value=rel if rel in third_party_files else third_party_files[0],
                label="Third-party document",
                on_change=_on_third_pick,
            ).classes("w-full")

    body = ui.column().classes("w-full min-w-0 mt-6")
    render_one_file(body, root, rel, static_url=static_url)
