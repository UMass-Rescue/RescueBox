import sys

from nicegui import ui

from .dialogs import (
    show_conversation_view_dialog,
    show_help_dialog,
    show_history_dialog,
)
from .rendering import (
    render_conversation_card,
    render_message_card,
    render_message_in_dialog,
    render_welcome_message,
)
from .ui_elements import create_chat_header, create_chat_window, create_input_area
from .ui_operations import UIOperations
from .utils import get_latest_input_area, set_latest_input_area
from .view import load_conversation, rerun_tool_call, view_conversation
from . import rendering as conversation_renderer
from . import utils as conversation_utils
from . import view as conversation_actions

history_panel = sys.modules[__name__]
__all__ = [
    "UIOperations",
    "set_latest_input_area",
    "get_latest_input_area",
    "render_welcome_message",
    "render_message_card",
    "render_conversation_card",
    "render_message_in_dialog",
    "create_chat_header",
    "create_chat_window",
    "create_input_area",
    "show_help_dialog",
    "show_history_dialog",
    "show_conversation_view_dialog",
    "view_conversation",
    "load_conversation",
    "rerun_tool_call",
    "ui",
    "conversation_actions",
    "conversation_renderer",
    "conversation_utils",
    "history_panel",
]
