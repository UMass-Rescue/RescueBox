from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token

from nicegui import app, ui

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.utils.ui import is_ephemeral_ui_error

_chat_container_override: ContextVar[ui.element | None] = ContextVar(
    "chat_container_override", default=None
)


@contextmanager
def chat_container_scope(container: ui.element | None) -> Iterator[None]:
    """Temporarily treat ``container`` as the resolved chat target for this task."""
    tok: Token = _chat_container_override.set(container)
    try:
        yield
    finally:
        _chat_container_override.reset(tok)


def get_global_chat_container() -> ui.element | None:
    """Fallback to get the global chat container from storage if possible."""
    # In V3, we mostly rely on the state manager, but tests might still look for this
    return app.storage.user.get("global_chat_container")


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


def safe_ui_call(func, *args, **kwargs):
    """Safely call a UI function, swallowing ephemeral UI errors."""

    def handle_error(e):
        if is_ephemeral_ui_error(e):
            return
        raise e

    if asyncio.iscoroutinefunction(func):

        async def async_wrapper():
            try:
                return await func(*args, **kwargs)
            except UI_RENDER_ERRORS as e:
                return handle_error(e)

        return async_wrapper()

    try:
        return func(*args, **kwargs)
    except UI_RENDER_ERRORS as e:
        return handle_error(e)
