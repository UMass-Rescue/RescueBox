from nicegui import background_tasks

from frontend.chatbot import api_helpers
from frontend.chatbot.config import ChatbotConfig, ToolRegistry
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.message_handler import MessageHandler
from frontend.chatbot.multi_tool_handler import (
    apply_metadata_filter,
    batch_items_have_age_gender_metadata,
    chain_output_to_input,
    coerce_pipeline_response,
    extract_batch_file_items,
)
from frontend.components.chat.utils import UIOperations
from frontend.database.chat_history_db import get_chat_history_db
from frontend.database.job_db import get_job_db

from .coordinator import (
    FormSubmitHandler,
    MessageFlowCoordinator,
    MessageProcessor,
    PipelineHandler,
    ResultProcessor,
)
from .database_service import DatabaseService
from .handlers import JobSubmissionOrchestrator
from .state import ChatbotStateManager, ChatMessage
from .ui import (
    ChatbotPage,
    _show_results_body,
    chatbot_page,
    create_chat_ui,
    handle_api_error,
    handle_rerun_parameter,
    load_and_show_form,
    render_message,
    show_error_to_user,
    show_results,
    show_tool_selection,
)
from .utils import is_ephemeral_ui_error, resolve_chat_container, safe_ui_call

database_service = DatabaseService()

__all__ = [
    'ChatbotStateManager',
    'ChatMessage',
    'MessageFlowCoordinator',
    'FormSubmitHandler',
    'ResultProcessor',
    'MessageProcessor',
    'PipelineHandler',
    'ChatbotPage',
    'chatbot_page',
    'create_chat_ui',
    'render_message',
    'show_results',
    'load_and_show_form',
    'JobSubmissionOrchestrator',
    'resolve_chat_container',
    'is_ephemeral_ui_error',
    'safe_ui_call',
    'show_error_to_user',
    'handle_api_error',
    '_show_results_body',
    'show_tool_selection',
    'DatabaseService',
    'database_service',
    'background_tasks',
    'get_chat_history_db',
    'get_job_db',
    'handle_rerun_parameter',
    'ChatbotCore',
    'ChatbotConfig',
    'MessageHandler',
    'ToolRegistry',
    'api_helpers',
    'coerce_pipeline_response',
    'chain_output_to_input',
    'extract_batch_file_items',
    'apply_metadata_filter',
    'batch_items_have_age_gender_metadata',
    'UIOperations'
]
