"""In-app walkthrough: Other plugins & multi-step pipeline (Markdown in frontend/demo/)."""

from __future__ import annotations

from frontend.constants import NAV_LINKS, UI_TITLES, demo_samples_url
from frontend.pages.demo_walkthrough_layout import register_demo_walkthrough_route

_MD_FILE = "other_walkthrough.md"
_SHORTCUTS = (
    ("Demo home", NAV_LINKS["demo"]),
    ("Same samples on Demo", demo_samples_url("other")),
    ("Assistant", NAV_LINKS["chatbot"]),
    ("Jobs", NAV_LINKS["jobs"]),
)

register_demo_walkthrough_route(
    "/demo/other-walkthrough",
    _MD_FILE,
    _SHORTCUTS,
    icon="extension",
    title="Interesting plugins & pipeline walkthrough",
    log_label="Other",
    extra_footer_links=[
        ("Open Assistant", NAV_LINKS["chatbot"]),
        (UI_TITLES["jobs"], NAV_LINKS["jobs"]),
    ],
)
