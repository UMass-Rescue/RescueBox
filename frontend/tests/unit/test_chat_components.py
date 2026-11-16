"""Smoke tests for ``frontend.components.chat`` concrete modules and public exports."""

import pytest

import frontend.components.chat as chat_pkg
from frontend.components.chat import rendering, utils, view


def test_concrete_chat_submodules_resolve():
    """Verify concrete submodules are directly imported and match package attributes."""
    assert view is chat_pkg.view
    assert rendering is chat_pkg.rendering
    assert utils is chat_pkg.utils


@pytest.mark.parametrize(
    "import_path, symbol",
    [
        ("frontend.components.chat", "view_conversation"),
        ("frontend.components.chat", "load_conversation"),
        ("frontend.components.chat", "rerun_tool_call"),
        ("frontend.components.chat", "render_message_in_dialog"),
        ("frontend.components.chat.view", "view_conversation"),
        ("frontend.components.chat.view", "load_conversation"),
        ("frontend.components.chat.view", "rerun_tool_call"),
        ("frontend.components.chat.rendering", "render_message_in_dialog"),
    ],
)
def test_chat_symbols_are_exported(import_path: str, symbol: str):
    mod = __import__(import_path, fromlist=[symbol])
    assert callable(getattr(mod, symbol))
