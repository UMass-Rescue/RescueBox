"""In-app walkthrough: Other plugins & multi-step pipeline (Markdown in frontend/demo/)."""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.demo import (
    load_markdown_file,
    render_guided_markdown_body,
    schedule_hash_fragment_scroll,
)
from frontend.components.shared import create_navbar
from frontend.constants import NAV_LINKS, UI_TITLES, demo_samples_url

logger = logging.getLogger(__name__)

_MD_FILE = "other_walkthrough.md"


def _fallback_markdown() -> str:
    return f"""## Missing walkthrough file

Could not read `{_MD_FILE}`. Add `frontend/demo/{_MD_FILE}` to customize this page.

**Shortcuts:** [Demo home]({NAV_LINKS["demo"]}) · [Same samples on Demo]({demo_samples_url("other")}) · [Assistant]({NAV_LINKS["chatbot"]}) · [Jobs]({NAV_LINKS["jobs"]})
"""


@ui.page("/demo/other-walkthrough")
async def demo_other_walkthrough_page():
    """Age/gender, deepfake, prompts, and pipeline + filter dialog guide."""
    from frontend.utils import apply_saved_theme

    apply_saved_theme()
    create_navbar()
    from frontend.utils import require_demo_user_session

    if not require_demo_user_session():
        return

    text = load_markdown_file(_MD_FILE, _fallback_markdown)

    with ui.column().classes(
        "container mx-auto px-4 sm:px-8 py-8 w-full max-w-4xl pb-16"
    ):
        with ui.row().classes("items-center gap-2 mb-2"):
            ui.icon("extension", size="lg").classes("text-[#881c1c]")
            ui.label("Interesting plugins & pipeline walkthrough").classes(
                "text-4xl font-bold text-slate-800"
            )

        render_guided_markdown_body(ui.column().classes("w-full min-w-0"), text)

        # render_walkthrough_samples_panel(ui.column().classes("w-full min-w-0"), "other")

        with ui.row().classes("gap-4 flex-wrap items-center mt-8"):
            ui.button(
                "Back to Demo",
                icon="arrow_back",
                on_click=lambda: ui.navigate.to(NAV_LINKS["demo"]),
            ).classes(
                "bg-slate-100 hover:bg-slate-200 text-slate-800 px-4 py-2 rounded-lg font-medium transition-colors border border-slate-200"
            )

            ui.link("Open Assistant", NAV_LINKS["chatbot"]).classes(
                "text-[#881c1c] hover:underline font-medium"
            )
            ui.link(UI_TITLES["jobs"], NAV_LINKS["jobs"]).classes(
                "text-[#881c1c] hover:underline font-medium"
            )

    schedule_hash_fragment_scroll()
    logger.debug("Other walkthrough page rendered")
