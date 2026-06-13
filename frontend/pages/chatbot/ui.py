"""Chatbot UI public exports and NiceGUI route registration."""

from __future__ import annotations

from frontend.components.chat import ui_bridge
from frontend.pages.chatbot.chat_page import ChatbotPage
from frontend.utils import handle_api_error, show_error_to_user
from frontend.pages.chatbot.routes import (
    chatbot_page,
    create_chat_ui,
    handle_rerun_parameter,
)
from frontend.pages.chatbot.history_ui import render_message
from frontend.pages.chatbot.ui_builder import ChatUIBuilder, FormConfig

_PATCHABLE_UI_NAMES = (
    "badge",
    "button",
    "card",
    "chat_message",
    "code",
    "column",
    "element",
    "expansion",
    "icon",
    "label",
    "navigate",
    "notify",
    "row",
    "separator",
    "timer",
)

__all__ = [
    "ChatbotPage",
    "chatbot_page",
    "create_chat_ui",
    "render_message",
    "show_error_to_user",
    "handle_api_error",
    "handle_rerun_parameter",
    "ChatUIBuilder",
    "FormConfig",
    *list(_PATCHABLE_UI_NAMES),
]

for _export_name in _PATCHABLE_UI_NAMES:
    globals()[_export_name] = getattr(ui_bridge, _export_name)

del _export_name, _PATCHABLE_UI_NAMES, ui_bridge
