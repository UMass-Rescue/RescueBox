"""
In-app quick start guide. Content is loaded from frontend/demo/quick_start.md (editable).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from nicegui import ui

from frontend.components.shared import create_navbar
from frontend.constants import NAV_LINKS, UI_TITLES

logger = logging.getLogger(__name__)

_QUICK_START_MD = Path(__file__).resolve().parent.parent / "demo" / "quick_start.md"

_SCREENSHOT_LINE = re.compile(r"^\{\{SCREENSHOT:([^}]+)\}\}\s*$", re.MULTILINE)


def _strip_editor_comment(text: str) -> str:
    return re.sub(r"^\s*<!--.*?-->\s*", "", text, count=1, flags=re.DOTALL)


def _fallback_markdown() -> str:
    """Used if quick_start.md is missing."""
    return f"""## Missing quick start file

Could not read `{_QUICK_START_MD}`. Add that Markdown file to customize this page.

**Shortcuts:** [Browse Plugins]({NAV_LINKS["models"]}) · [Assistant]({NAV_LINKS["chatbot"]}) · [Jobs]({NAV_LINKS["jobs"]}) · [Demo]({NAV_LINKS["demo"]})
"""


def _load_markdown_source() -> str:
    if _QUICK_START_MD.is_file():
        try:
            return _strip_editor_comment(_QUICK_START_MD.read_text(encoding="utf-8"))
        except OSError as e:
            logger.warning("Could not read quick_start.md: %s", e)
    return _fallback_markdown()


def _iter_md_and_images(text: str):
    """Split markdown on {{SCREENSHOT:file.png}} lines; yield ('md', str) or ('img', filename)."""
    pos = 0
    found = False
    for m in _SCREENSHOT_LINE.finditer(text):
        found = True
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
    if not found and text.strip():
        yield ("md", text.strip())


def _render_quick_start_body(container: ui.element) -> None:
    text = _load_markdown_source()
    segments = list(_iter_md_and_images(text))
    if not segments:
        ui.label("Quick start content is empty.").classes("text-gray-500")
        return
    with container:
        for kind, payload in segments:
            if kind == "md":
                ui.markdown(payload).classes("prose prose-slate max-w-none")
            else:
                safe = Path(payload).name
                if safe != payload or ".." in payload or "/" in payload or "\\" in payload:
                    logger.warning("Ignoring unsafe screenshot name: %s", payload)
                    continue
                ui.image(f"/demo/{safe}").classes(
                    "w-full max-w-3xl rounded-lg border border-gray-200 shadow-md my-4"
                )


@ui.page("/demo/quick-start")
async def demo_quick_start_page():
    """Scrollable quick start from frontend/demo/quick_start.md."""
    from frontend.utils.theme import apply_saved_theme

    apply_saved_theme()
    create_navbar()

    with ui.column().classes("container mx-auto p-8 max-w-4xl w-full min-w-0 pb-16"):
        ui.label("RescueBox quick start").classes("text-3xl font-bold mb-2")

        _render_quick_start_body(ui.column().classes("w-full min-w-0"))

        with ui.row().classes("gap-4 flex-wrap items-center mt-8"):
            ui.button(
                "Back to Demo",
                on_click=lambda: ui.navigate.to(NAV_LINKS["demo"]),
            ).classes("bg-blue-600 text-white")
            ui.link("Browse Plugins", NAV_LINKS["models"]).classes("text-blue-600 hover:underline")
            ui.link(UI_TITLES["chatbot"], NAV_LINKS["chatbot"]).classes(
                "text-blue-600 hover:underline"
            )
            ui.link(UI_TITLES["jobs"], NAV_LINKS["jobs"]).classes("text-blue-600 hover:underline")

    logger.debug("Quick start page rendered")
