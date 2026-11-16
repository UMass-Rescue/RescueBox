from __future__ import annotations

from contextvars import ContextVar
from nicegui import app, ui
from frontend.utils.ui import is_ephemeral_ui_error, safe_ui_call

_chat_container_override: ContextVar[ui.element | None] = ContextVar(
    "chat_container_override", default=None
)


def get_global_chat_container() -> ui.element | None:
    """Fallback to get the global chat container from storage if possible."""
    # In V3, we mostly rely on the state manager, but tests might still look for this
    try:
        return app.storage.user.get("global_chat_container")
    except Exception:
        return None


def resolve_chat_container(
    explicit: ui.element | None = None,
    *,
    prefer_session_global: bool = False,
) -> ui.element | None:
    """
    Return the chat message area to render into.
    Resolution order: explicit -> contextvar override -> session global.
    """
    g = get_global_chat_container()
    override = _chat_container_override.get()

    if prefer_session_global:
        return g or explicit or override

    if explicit is not None:
        return explicit
    if override is not None:
        return override
    return g

__all__ = [
    "get_global_chat_container",
    "is_ephemeral_ui_error",
    "resolve_chat_container",
    "safe_ui_call",
]
