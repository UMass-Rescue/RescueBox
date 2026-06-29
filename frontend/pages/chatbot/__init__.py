"""Public exports for chatbot page stack and helpers."""

from nicegui import background_tasks

from frontend.chatbot import api_helpers
from frontend.chatbot.config import ChatbotConfig, ToolRegistry
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.message_handler import MessageHandler
from frontend.components.chat import UIOperations

from . import handlers
from .coordinator import (
    FormSubmitHandler,
    MessageFlowCoordinator,
    MessageProcessor,
    ResultProcessor,
)
from .database_service import DatabaseService
from .handlers import JobSubmissionOrchestrator, PipelineHandler
from .state import ChatbotStateManager, ChatMessage
from .ui import (
    ChatbotPage,
    chatbot_page,
    create_chat_ui,
    handle_api_error,
    handle_rerun_parameter,
    render_message,
    show_error_to_user,
)
from .ui_flow import (
    _show_results_body,
    load_and_show_form,
    show_results,
    show_tool_selection,
)
from .utils import is_ephemeral_ui_error, resolve_chat_container, safe_ui_call

database_service = DatabaseService()

__all__ = [
    "ChatbotStateManager",
    "ChatMessage",
    "MessageFlowCoordinator",
    "FormSubmitHandler",
    "ResultProcessor",
    "MessageProcessor",
    "PipelineHandler",
    "handlers",
    "ChatbotPage",
    "chatbot_page",
    "create_chat_ui",
    "render_message",
    "show_results",
    "load_and_show_form",
    "JobSubmissionOrchestrator",
    "resolve_chat_container",
    "is_ephemeral_ui_error",
    "safe_ui_call",
    "show_error_to_user",
    "handle_api_error",
    "_show_results_body",
    "show_tool_selection",
    "DatabaseService",
    "database_service",
    "handle_rerun_parameter",
    # Compatibility exports for existing test patch paths.
    "background_tasks",
    "ChatbotCore",
    "ChatbotConfig",
    "MessageHandler",
    "ToolRegistry",
    "api_helpers",
    "UIOperations",
]
