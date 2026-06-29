"""Smoke tests for ``frontend.components.chat`` public exports."""

import pytest

import frontend.components.chat as chat_pkg


def test_backward_compat_chat_submodules_resolve():
    from frontend.components.chat import (
        conversation_actions,
        conversation_renderer,
        conversation_utils,
        history_panel,
    )

    assert conversation_actions is chat_pkg.view
    assert conversation_renderer is chat_pkg.rendering
    assert conversation_utils is chat_pkg.utils
    assert history_panel is chat_pkg


@pytest.mark.parametrize(
    "import_path, symbol",
    [
        ("frontend.components.chat", "view_conversation"),
        ("frontend.components.chat", "load_conversation"),
        ("frontend.components.chat", "rerun_tool_call"),
        ("frontend.components.chat", "render_message_in_dialog"),
    ],
)
def test_chat_symbols_are_exported(import_path: str, symbol: str):
    mod = __import__(import_path, fromlist=[symbol])
    assert callable(getattr(mod, symbol))
