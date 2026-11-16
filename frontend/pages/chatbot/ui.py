"""Chatbot UI public exports and NiceGUI route registration."""

from __future__ import annotations

from frontend.components.chat.ui_bridge import (
    badge,
    button,
    card,
    chat_message,
    code,
    column,
    element,
    expansion,
    icon,
    label,
    markdown,
    navigate,
    notify,
    row,
    separator,
    timer,
)
from frontend.pages.chatbot.chat_page import ChatbotPage
from frontend.pages.chatbot.history_ui import render_message
from frontend.pages.chatbot.routes import (
    chatbot_page,
    create_chat_ui,
    handle_rerun_parameter,
)
from frontend.pages.chatbot.ui_builder import ChatUIBuilder, FormConfig
from frontend.utils import handle_api_error, show_error_to_user

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
    "markdown",
    "navigate",
    "notify",
    "row",
    "separator",
    "timer",
]
