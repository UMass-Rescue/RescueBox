"""In-app quick start guide. Content is loaded from frontend/demo/quick_start.md (editable)."""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.demo import load_markdown_file
from frontend.constants import NAV_LINKS, demo_samples_url
from frontend.pages.demo_walkthrough_layout import (
    begin_demo_walkthrough_page,
    missing_walkthrough_markdown,
    render_demo_walkthrough_content,
)

logger = logging.getLogger(__name__)

_QUICK_START_MD = "quick_start.md"
_SHORTCUTS = (
    ("Browse Plugins", NAV_LINKS["models"]),
    ("Assistant", NAV_LINKS["chatbot"]),
    ("Jobs", NAV_LINKS["jobs"]),
    ("Demo home", NAV_LINKS["demo"]),
    ("Demo samples (quick start)", demo_samples_url("quick_start")),
)


@ui.page("/demo/quick-start")
async def demo_quick_start_page():
    """Scrollable quick start from frontend/demo/quick_start.md."""
    if not begin_demo_walkthrough_page():
        return

    text = load_markdown_file(
        _QUICK_START_MD,
        lambda: missing_walkthrough_markdown(_QUICK_START_MD, _SHORTCUTS),
    )
    render_demo_walkthrough_content(
        icon="rocket_launch",
        title="RescueBox quick start",
        markdown_body=text,
        log_label="Quick start",
        extra_footer_links=[
            ("Demo samples", demo_samples_url("quick_start")),
        ],
    )
