"""In-app walkthrough: Image summary via Assistant prompt (Markdown in frontend/demo/)."""

from __future__ import annotations

from frontend.constants import NAV_LINKS, demo_samples_url
from frontend.pages.demo_walkthrough_layout import register_demo_walkthrough_route

_MD_FILE = "image_search_walkthrough.md"
_SHORTCUTS = (
    ("Demo home", NAV_LINKS["demo"]),
    ("Same samples on Demo", demo_samples_url("image_search")),
    ("Assistant", NAV_LINKS["chatbot"]),
    ("Jobs", NAV_LINKS["jobs"]),
)

register_demo_walkthrough_route(
    "/demo/image-search-walkthrough",
    _MD_FILE,
    _SHORTCUTS,
    icon="image",
    title="Search Image — Assistant prompt walkthrough",
    log_label="Image search",
)
