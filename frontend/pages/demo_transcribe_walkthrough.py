"""
In-app walkthrough: Transcribe via Assistant tool picker (Markdown in frontend/demo/).
"""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.demo.demo_files_explorer import render_walkthrough_samples_panel
from frontend.components.demo.guided_markdown import (
    load_markdown_file,
    render_guided_markdown_body,
    schedule_hash_fragment_scroll,
)
from frontend.components.shared import create_navbar
from frontend.constants import NAV_LINKS, UI_TITLES, demo_samples_url

logger = logging.getLogger(__name__)

_MD_FILE = "transcribe_walkthrough.md"


def _fallback_markdown() -> str:
    return f"""## Missing walkthrough file

Could not read `{_MD_FILE}`. Add `frontend/demo/{_MD_FILE}` to customize this page.

**Shortcuts:** [Demo home]({NAV_LINKS["demo"]}) · [Same samples on Demo]({demo_samples_url("transcribe")}) · [Assistant]({NAV_LINKS["chatbot"]}) · [Jobs]({NAV_LINKS["jobs"]})
"""


@ui.page("/demo/transcribe-walkthrough")
async def demo_transcribe_walkthrough_page():
    """Step-by-step transcribe (tool picker) guide."""
    from frontend.utils.theme import apply_saved_theme

    apply_saved_theme()
    create_navbar()
    from frontend.utils.demo_user_gate import require_demo_user_session

    if not require_demo_user_session():
        return

    text = load_markdown_file(_MD_FILE, _fallback_markdown)

    with ui.column().classes("container mx-auto p-8 max-w-4xl w-full min-w-0 pb-16"):
        ui.label("Transcribe — tool menu walkthrough").classes("text-3xl font-bold mb-2")

        render_guided_markdown_body(ui.column().classes("w-full min-w-0"), text)

        # render_walkthrough_samples_panel(ui.column().classes("w-full min-w-0"), "transcribe")

        with ui.row().classes("gap-4 flex-wrap items-center mt-8"):
            ui.button(
                "Back to Demo",
                on_click=lambda: ui.navigate.to(NAV_LINKS["demo"]),
            ).classes("rb-brand-primary text-white")

    schedule_hash_fragment_scroll()
    logger.debug("Transcribe walkthrough page rendered")
