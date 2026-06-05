"""In-app quick start guide. Content is loaded from frontend/demo/quick_start.md (editable)."""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.demo import (
    load_markdown_file,
    render_guided_markdown_body,
    schedule_hash_fragment_scroll,
)
from frontend.components.shared import create_navbar
from frontend.constants import NAV_LINKS, demo_samples_url

logger = logging.getLogger(__name__)

_QUICK_START_MD = "quick_start.md"


def _fallback_markdown() -> str:
    """Used if quick_start.md is missing."""
    return f"""## Missing quick start file

Could not read `frontend/demo/{_QUICK_START_MD}`. Add that Markdown file to customize this page.

**Shortcuts:** [Browse Plugins]({NAV_LINKS["models"]}) · [Assistant]({NAV_LINKS["chatbot"]}) · [Jobs]({NAV_LINKS["jobs"]}) · [Demo home]({NAV_LINKS["demo"]}) · [Demo samples (quick start)]({demo_samples_url("quick_start")})
"""


@ui.page("/demo/quick-start")
async def demo_quick_start_page():
    """Scrollable quick start from frontend/demo/quick_start.md."""
    from frontend.utils import apply_saved_theme

    apply_saved_theme()
    create_navbar()
    from frontend.utils import require_demo_user_session

    if not require_demo_user_session():
        return

    text = load_markdown_file(_QUICK_START_MD, _fallback_markdown)

    with ui.column().classes("container mx-auto px-4 sm:px-8 py-8 w-full max-w-4xl pb-16"):
        with ui.row().classes("items-center gap-2 mb-2"):
            ui.icon("rocket_launch", size="lg").classes("text-[#881c1c]")
            ui.label("RescueBox quick start").classes("text-4xl font-bold text-slate-800")

        render_guided_markdown_body(ui.column().classes("w-full min-w-0"), text)

        # render_walkthrough_samples_panel(ui.column().classes("w-full min-w-0"), "quick_start")

        with ui.row().classes("gap-4 flex-wrap items-center mt-8"):
            ui.button(
                "Back to Demo",
                icon="arrow_back",
                on_click=lambda: ui.navigate.to(NAV_LINKS["demo"]),
            ).classes("bg-slate-100 hover:bg-slate-200 text-slate-800 px-4 py-2 rounded-lg font-medium transition-colors border border-slate-200")

            ui.link("Demo samples", demo_samples_url("quick_start")).classes(
                "text-[#881c1c] hover:underline text-sm font-medium"
            )

    schedule_hash_fragment_scroll()
    logger.debug("Quick start page rendered")
