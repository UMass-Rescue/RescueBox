"""Load and render License&Copyright documents (shared by About and /licenses redirect)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional
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
                "text-sm text-gray-500 font-mono mb-2"
            )
            ui.code(raw).classes(
                "w-full max-w-none text-sm whitespace-pre-wrap break-words "
                "block p-4 bg-gray-50 rounded border border-gray-200"
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
        "Third-party and bundled component notices from the repository’s License&Copyright folder."
    ).classes("text-sm text-gray-600 mb-4")

    if not root.is_dir():
        ui.label(f"Folder not found: {root}").classes("text-red-600")
        return
    if not files:
        ui.label("No license documents found in that folder.").classes("text-gray-600")
        return

    rel = unquote(doc) if doc else ""
    if rel not in files:
        rel = files[0]

    base = page_path.rstrip("/") or "/about"

    def _on_pick(e) -> None:
        new_rel = e.value
        if isinstance(new_rel, str) and new_rel in files:
            ui.navigate.to(f"{base}?doc={quote(new_rel, safe='')}")

    ui.select(
        options=files,
        value=rel,
        label="Document",
        on_change=_on_pick,
    ).classes("w-full max-w-2xl")

    body = ui.column().classes("w-full min-w-0 mt-6")
    render_one_file(body, root, rel, static_url=static_url)
