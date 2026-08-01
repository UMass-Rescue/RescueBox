"""Tool-selection card shown in chat when a plugin run starts."""

from __future__ import annotations

import logging
import weakref

from nicegui import ui

from frontend.chatbot.config import ToolRegistry
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)

_ACTIVE_TOOL_SELECTION_CARDS = weakref.WeakSet()


def render_tool_selection_message(container: ui.element, endpoint: str):
    plugin_label = ToolRegistry.display_name_for_endpoint(endpoint)
    logger.debug(
        "Rendering tool selection card for endpoint=%s label=%s into container=%r",
        endpoint,
        plugin_label,
        container,
    )
    with container:
        card = ui.card().classes(
            "w-full max-w-2xl bg-white ring-1 ring-zinc-200 shadow-sm rounded-2xl rounded-tl-none"
        )
        with card, ui.column().classes("p-4 gap-2 w-full min-w-0"):
            ui.label("Assistant").classes(
                "font-semibold !text-sm text-zinc-500 uppercase tracking-wide"
            )
            ui.label(f"Running {plugin_label} operation.").classes(
                "!text-base sm:!text-lg leading-snug text-zinc-800"
            )
    try:
        _ACTIVE_TOOL_SELECTION_CARDS.add(card)
    except UI_RENDER_ERRORS:
        pass
    return card


def clear_active_tool_selection_cards() -> None:
    try:
        for c in list(_ACTIVE_TOOL_SELECTION_CARDS):
            try:
                c.delete()
            except UI_RENDER_ERRORS:
                pass
        _ACTIVE_TOOL_SELECTION_CARDS.clear()
    except UI_RENDER_ERRORS:
        pass
