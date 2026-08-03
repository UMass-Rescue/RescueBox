"""Common page chrome: loading rows, cards, headers."""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.component_utils import create_success_card_element
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.utils.ui import _safe_ui_call

logger = logging.getLogger(__name__)


def render_loading_row(message: str = "Loading..."):
    """Render a small loading row with spinner and label."""
    row = _safe_ui_call(ui.row)
    if not row:
        return None
    with row.classes("items-center gap-2"):
        ui.spinner(size="sm")
        ui.label(message).classes("text-sm text-zinc-600")
    return row


def render_error_card(container, message: str):
    """Render an error card inside the given container."""
    with container:
        with ui.card().classes("bg-red-50 border border-red-300 p-4") as error_card:
            ui.label("Error").classes("text-lg font-semibold text-red-700 mb-2")
            ui.label(message).classes("text-red-600")
    return error_card


def render_success_card(container, message: str):
    """Render a success card inside the given container."""
    with container:
        return create_success_card_element(message)


def render_page_header(title: str, actions_callable: callable | None = None):
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
