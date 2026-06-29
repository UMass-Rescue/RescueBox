"""Shared page shell helpers (theme, navbar, compact CSS)."""

from __future__ import annotations

from frontend.components.shared import create_navbar
from frontend.utils import apply_saved_theme, require_demo_user_session

COMPACT_TOOLBAR_HEAD_HTML = """
        <style>
            .q-header { min-height: 54px !important; }
            .q-toolbar { min-height: 54px !important; padding: 0 16px !important; }
            .q-toolbar__title {
                font-size: 1.2rem !important;
                min-height: unset !important;
                line-height: 54px !important;
            }
            .q-btn {
                font-size: 0.95rem !important;
                padding: 6px 12px !important;
                min-height: unset !important;
            }
            body { font-size: 1.05rem !important; }
        </style>
    """


def begin_demo_session_page() -> bool:
    """Apply theme, navbar, and demo-user gate. Returns False if the page should stop."""
    apply_saved_theme()
    create_navbar()
    return require_demo_user_session()
