"""
Helpers for NiceGUI calls that often fail when the browser client is gone
(refresh, navigation, tab closed).

Centralizes substring checks so call sites can use one predicate instead of
copy-pasting ``'deleted' in str(e)``.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Substrings observed when UI work is no longer valid (not user errors).
_EPHEMERAL_MARKERS: tuple[str, ...] = (
    "deleted",
    "slot cannot be determined",
    "client has been deleted",
    "the client is gone",
)


def is_ephemeral_ui_error(exc: BaseException) -> bool:
    """True if ``exc`` indicates the NiceGUI client/session is no longer available."""
    msg = str(exc).lower()
    return any(m in msg for m in _EPHEMERAL_MARKERS)


def log_ephemeral_ui(logger_: logging.Logger, msg: str, exc: BaseException) -> None:
    """Log at DEBUG for ephemeral UI errors (single pattern for callers)."""
    logger_.debug("%s: %s", msg, exc)


def safe_ui_call(
    fn: Callable[..., Any],
    *args: Any,
    on_ephemeral: Optional[Callable[[BaseException], None]] = None,
    **kwargs: Any,
) -> Any:
    """
    Run a synchronous callable; swallow only **ephemeral** UI errors.

    Returns ``None`` if the error was swallowed; re-raises other exceptions.
    """
    try:
        return fn(*args, **kwargs)
    except BaseException as e:
        if is_ephemeral_ui_error(e):
            if on_ephemeral:
                on_ephemeral(e)
            else:
                log_ephemeral_ui(logger, "safe_ui_call suppressed", e)
            return None
        raise


async def safe_ui_await(awaitable: Any) -> Any:
    """Await a coroutine; swallow ephemeral UI errors (returns ``None``)."""
    try:
        return await awaitable
    except BaseException as e:
        if is_ephemeral_ui_error(e):
            log_ephemeral_ui(logger, "safe_ui_await suppressed", e)
            return None
        raise
