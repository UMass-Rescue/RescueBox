import logging
from nicegui import ui
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Keep a weak set of active selection cards so we can aggressively clear any orphaned cards.
import weakref
_ACTIVE_TOOL_SELECTION_CARDS = weakref.WeakSet()


def render_tool_selection_message(container: ui.element, endpoint: str):
    """
    Render a small tool selection message card indicating the selected tool.
    Returns the created card element so the caller can manage its lifecycle.
    """
    logger.debug("Rendering tool selection card for endpoint=%s into container=%r", endpoint, container)
    # Create the card inside the (chat area) provided container context to avoid creating it
    # in the currently active UI context (which could be an input-area wrapper).
    with container:
        card = ui.card().classes('w-full max-w-sm bg-blue-50 shadow-sm')
        with card:
            with ui.row().classes('p-3 items-center gap-2 flex-wrap'):
                ui.label('🤖 Assistant').classes('font-medium text-sm')
                ui.label(f"I'll use {endpoint} to help you.").classes('')
                ui.label('🔧 Selected Tool').classes('font-medium text-sm')
                ui.label(endpoint).classes('text-sm text-gray-600')
    try:
        _ACTIVE_TOOL_SELECTION_CARDS.add(card)
    except Exception:
        pass
    return card


def clear_active_tool_selection_cards():
    """Aggressively delete any active tool selection cards known globally."""
    try:
        for c in list(_ACTIVE_TOOL_SELECTION_CARDS):
            try:
                c.delete()
            except Exception:
                pass
        _ACTIVE_TOOL_SELECTION_CARDS.clear()
    except Exception:
        pass
