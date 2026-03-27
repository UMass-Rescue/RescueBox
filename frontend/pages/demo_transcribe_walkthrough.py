"""
In-app walkthrough: Transcribe via Assistant tool picker (Markdown in frontend/demo/).
"""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.demo.guided_markdown import load_markdown_file, render_guided_markdown_body
from frontend.components.shared import create_navbar
from frontend.constants import NAV_LINKS, UI_TITLES

logger = logging.getLogger(__name__)

_MD_FILE = "transcribe_walkthrough.md"


def _fallback_markdown() -> str:
    return f"""## Missing walkthrough file

Could not read `{_MD_FILE}`. Add `frontend/demo/{_MD_FILE}` to customize this page.

**Shortcuts:** [Demo](/demo) · [Assistant]({NAV_LINKS["chatbot"]}) · [Jobs]({NAV_LINKS["jobs"]})
"""


@ui.page("/demo/transcribe-walkthrough")
async def demo_transcribe_walkthrough_page():
    """Step-by-step transcribe (tool picker) guide."""
    from frontend.utils.theme import apply_saved_theme

    apply_saved_theme()
    create_navbar()

    text = load_markdown_file(_MD_FILE, _fallback_markdown)

    with ui.column().classes("container mx-auto p-8 max-w-4xl w-full min-w-0 pb-16"):
        ui.label("Transcribe — tool picker walkthrough").classes("text-3xl font-bold mb-2")

        render_guided_markdown_body(ui.column().classes("w-full min-w-0"), text)

        with ui.row().classes("gap-4 flex-wrap items-center mt-8"):
            ui.button(
                "Back to Demo",
                on_click=lambda: ui.navigate.to(NAV_LINKS["demo"]),
            ).classes("bg-blue-600 text-white")
            ui.link("Open Assistant", NAV_LINKS["chatbot"]).classes("text-blue-600 hover:underline")
            ui.link(UI_TITLES["jobs"], NAV_LINKS["jobs"]).classes("text-blue-600 hover:underline")

    logger.debug("Transcribe walkthrough page rendered")
