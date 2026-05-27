"""In-app walkthrough: Other plugins & multi-step pipeline (Markdown in frontend/demo/)."""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.demo import render_walkthrough_samples_panel
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

    with ui.column().classes("container mx-auto p-8 max-w-4xl w-full min-w-0 pb-16"):
        ui.label("Interesting plugins & pipeline walkthrough").classes("text-3xl font-bold mb-2")

        render_guided_markdown_body(ui.column().classes("w-full min-w-0"), text)

        # render_walkthrough_samples_panel(ui.column().classes("w-full min-w-0"), "other")

        with ui.row().classes("gap-4 flex-wrap items-center mt-8"):
            ui.button(
                "Back to Demo",
                on_click=lambda: ui.navigate.to(NAV_LINKS["demo"]),
            ).classes("rb-brand-primary text-white")
            
            ui.link("Open Assistant", NAV_LINKS["chatbot"]).classes("text-[#881c1c] hover:underline")
            ui.link(UI_TITLES["jobs"], NAV_LINKS["jobs"]).classes("text-[#881c1c] hover:underline")

    schedule_hash_fragment_scroll()
    logger.debug("Other walkthrough page rendered")
