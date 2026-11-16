"""Common page chrome: loading rows, cards, headers."""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Callable
import logging

from nicegui import ui

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.utils.ui import safe_ui_call

logger = logging.getLogger(__name__)


def render_loading_row(message: str = "Loading..."):
    """Render a small loading row with spinner and label."""
    row = safe_ui_call(ui.row, check_slot=True)
    if not row:
        return None
    with row.classes("items-center gap-2"):
        ui.spinner(size="sm")
        ui.label(message).classes("text-sm text-zinc-600")
    return row


def render_page_header(title: str, actions_callable: Callable | None = None):
    """Render a standardized page header with title and optional action buttons area."""
    with ui.row().classes("items-center justify-between w-full mb-6"):
        ui.label(title).classes("text-4xl font-bold")
        with ui.row().classes("gap-2"):
            if actions_callable:
                try:
                    actions_callable()
                except UI_RENDER_ERRORS as e:
                    logger.exception("Error rendering header actions: %s", e)
            else:
                # default placeholder
                ui.label("")
