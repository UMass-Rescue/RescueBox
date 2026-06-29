"""In-app walkthrough: Transcribe via Assistant tool picker (Markdown in frontend/demo/)."""

from __future__ import annotations

from frontend.constants import NAV_LINKS, demo_samples_url
from frontend.pages.demo_walkthrough_layout import register_demo_walkthrough_route

_MD_FILE = "transcribe_walkthrough.md"
_SHORTCUTS = (
    ("Demo home", NAV_LINKS["demo"]),
    ("Same samples on Demo", demo_samples_url("transcribe")),
    ("Assistant", NAV_LINKS["chatbot"]),
    ("Jobs", NAV_LINKS["jobs"]),
)

register_demo_walkthrough_route(
    "/demo/transcribe-walkthrough",
    _MD_FILE,
    _SHORTCUTS,
    icon="audiotrack",
    title="Transcribe — menu walkthrough",
    log_label="Transcribe",
)
