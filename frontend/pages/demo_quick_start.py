"""
In-app quick start guide. Content is loaded from frontend/demo/quick_start.md (editable).
"""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.demo.guided_markdown import load_markdown_file, render_guided_markdown_body
from frontend.components.shared import create_navbar
from frontend.constants import NAV_LINKS, UI_TITLES

logger = logging.getLogger(__name__)

_QUICK_START_MD = "quick_start.md"


def _fallback_markdown() -> str:
    """Used if quick_start.md is missing."""
    return f"""## Missing quick start file

Could not read `frontend/demo/{_QUICK_START_MD}`. Add that Markdown file to customize this page.

**Shortcuts:** [Browse Plugins]({NAV_LINKS["models"]}) · [Assistant]({NAV_LINKS["chatbot"]}) · [Jobs]({NAV_LINKS["jobs"]}) · [Demo]({NAV_LINKS["demo"]})
"""


@ui.page("/demo/quick-start")
async def demo_quick_start_page():
    """Scrollable quick start from frontend/demo/quick_start.md."""
    from frontend.utils.theme import apply_saved_theme

    apply_saved_theme()
    create_navbar()

    text = load_markdown_file(_QUICK_START_MD, _fallback_markdown)

    with ui.column().classes("container mx-auto p-8 max-w-4xl w-full min-w-0 pb-16"):
        ui.label("RescueBox quick start").classes("text-3xl font-bold mb-2")

        render_guided_markdown_body(ui.column().classes("w-full min-w-0"), text)

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
