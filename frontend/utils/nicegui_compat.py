"""
NiceGUI compatibility helpers.

Provide small wrappers that adapt to different NiceGUI call signatures and
silence type-checker mismatches inside the wrapper so callers remain clean.
"""
from typing import Any, Iterable
from nicegui import ui as _ui


def select(options: Iterable[Any], *args: Any, **kwargs: Any):
    """
    Compatibility wrapper for `ui.select`.

    Tries the keyword-argument form first and falls back to the positional
    form if the runtime raises a TypeError. The internal calls are ignored by
    the type-checker to avoid spurious signature errors from mismatched stubs.
    """
    try:
        # Prefer explicit keyword to match newer stubs; ignore type checking here.
        return _ui.select(options=options, *args, **kwargs)  # type: ignore[call-arg]
    except TypeError:
        # Fallback to positional if keyword form isn't accepted at runtime.
        return _ui.select(list(options), *args, **kwargs)  # type: ignore[call-arg]

