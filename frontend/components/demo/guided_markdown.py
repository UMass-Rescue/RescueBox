"""
Shared Markdown rendering for in-app guides (quick start, walkthroughs).

Screenshots: lines `{{SCREENSHOT:filename.png}}` load from `/demo/<filename>` (files in frontend/demo/).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Callable

from nicegui import ui

logger = logging.getLogger(__name__)

_FRONTEND_DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "demo"


def schedule_hash_fragment_scroll() -> None:
    """
    Scroll to the element whose id matches the URL fragment (e.g. /demo#sample-inputs,
    /demo/transcribe-walkthrough#walkthrough-samples). NiceGUI client-side navigation
    often does not perform native hash scrolling; this runs after paint.
    """
    js = """
        (function () {
            var id = (window.location.hash || '').replace(/^#/, '');
            if (!id) return;
            function tryScroll() {
                var el = document.getElementById(id);
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    return true;
                }
                return false;
            }
            if (!tryScroll()) {
                setTimeout(function () { tryScroll(); }, 200);
                setTimeout(function () { tryScroll(); }, 600);
            }
        })();
    """
    ui.timer(0.15, lambda: ui.run_javascript(js), once=True)
    ui.timer(0.5, lambda: ui.run_javascript(js), once=True)
_SCREENSHOT_LINE = re.compile(r"^\{\{SCREENSHOT:([^}]+)\}\}\s*$", re.MULTILINE)


def strip_editor_comment(text: str) -> str:
    return re.sub(r"^\s*<!--.*?-->\s*", "", text, count=1, flags=re.DOTALL)


def load_markdown_file(relative_name: str, fallback: Callable[[], str]) -> str:
    """Load ``frontend/demo/<relative_name>`` or use fallback."""
    path = _FRONTEND_DEMO_DIR / relative_name
    if path.is_file():
        try:
            return strip_editor_comment(path.read_text(encoding="utf-8"))
        except OSError as e:
            logger.warning("Could not read %s: %s", path, e)
    return fallback()


def iter_md_and_images(text: str):
    """Split markdown on {{SCREENSHOT:file.png}} lines; yield ('md', str) or ('img', filename)."""
    pos = 0
    matches = list(_SCREENSHOT_LINE.finditer(text))
    if not matches:
        # No screenshot directives: single markdown segment only (avoid duplicating full body)
        if text.strip():
            yield ("md", text.strip())
        return

    for m in matches:
        if m.start() > pos:
            chunk = text[pos : m.start()].strip()
            if chunk:
                yield ("md", chunk)
        yield ("img", m.group(1).strip())
        pos = m.end()
    if pos < len(text):
        tail = text[pos:].strip()
        if tail:
            yield ("md", tail)


def render_guided_markdown_body(container: ui.element, markdown_text: str) -> None:
    segments = list(iter_md_and_images(markdown_text))
    if not segments:
        ui.label("Guide content is empty.").classes("text-gray-500")
        return
    with container:
        for kind, payload in segments:
            if kind == "md":
                # Tailwind text-* on the element; use ! so global body { font-size: 0.8rem !important } does not win.
                ui.markdown(payload).classes(
                    "prose prose-slate max-w-none "
                    "!text-xl leading-relaxed "
                    "[&_p]:!text-xl [&_li]:!text-xl "
                    "[&_h1]:!text-3xl [&_h2]:!text-2xl [&_h3]:!text-2xl"
                )
            else:
                safe = Path(payload).name
                if safe != payload or ".." in payload or "/" in payload or "\\" in payload:
                    logger.warning("Ignoring unsafe screenshot name: %s", payload)
                    continue
                ui.image(f"/demo/{safe}").classes(
                    "w-full max-w-3xl rounded-lg border border-gray-200 shadow-md my-4"
                )
