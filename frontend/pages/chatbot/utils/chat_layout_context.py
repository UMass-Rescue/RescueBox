"""
Optional context override for which NiceGUI element is the active chat container.

Session storage still uses :func:`frontend.pages.chatbot.chatbot_forms.get_global_chat_container`
(keyed by user). This module adds a :class:`contextvars.ContextVar` so tests or
callers can push an explicit container without touching globals.

Resolution order: **explicit argument** → **contextvar override** → **per-user global**.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator, Optional

from nicegui import ui

_chat_container_override: ContextVar[Optional[ui.element]] = ContextVar(
    "chat_container_override", default=None
)


@contextmanager
def chat_container_scope(container: Optional[ui.element]) -> Iterator[None]:
    """Temporarily treat ``container`` as the resolved chat target for this task."""
    tok: Token = _chat_container_override.set(container)
    try:
        yield
    finally:
        _chat_container_override.reset(tok)


def resolve_chat_container(
    explicit: Optional[ui.element] = None,
    *,
    prefer_session_global: bool = False,
) -> Optional[ui.element]:
    """
    Return the chat message area to render into.

    Default (**prefer_session_global** False): **explicit** argument, then
    ``chat_container_scope`` override, then per-user global — matches
    ``explicit or get_global_chat_container()``.

    When **prefer_session_global** is True: per-user global first, then explicit
    (used where the main transcript should win over a nested wrapper container).
    """
    from frontend.pages.chatbot.chatbot_forms import get_global_chat_container

    g = get_global_chat_container()
    override = _chat_container_override.get()

    if prefer_session_global:
        return g or explicit or override

    if explicit is not None:
        return explicit
    if override is not None:
        return override
    return g
