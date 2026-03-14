"""
Message Service.

Handles message-related operations and conversions.
"""

import logging
from datetime import datetime
from typing import Type, TypeVar, Union
from nicegui import ui

from frontend.pages.chatbot.utils.ui_styling import UIStyling
from frontend.database.chat_history_db import ChatMessageRecord
from frontend.pages.chatbot.chatbot_message import ChatMessage, render_message
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Type variable for Pydantic models
PydanticModel = TypeVar('PydanticModel')


class MessageService:
    """Handles message-related operations and conversions."""

    @staticmethod
    def pydantic_to_dict(model) -> dict:
        """Convert Pydantic model to dict for JSON serialization."""
        if hasattr(model, 'model_dump'):
            return model.model_dump()
        elif hasattr(model, '__dict__'):
            return dict(model)
        else:
            return model

    @staticmethod
    def dict_to_pydantic(data, model_class: Type[PydanticModel]) -> Union[PydanticModel, dict]:
        """Convert dict to Pydantic model."""
        if isinstance(data, dict):
            try:
                return model_class(**data)
            except Exception as e:
                logger.warning(f"Failed to create {model_class.__name__} from dict {data}: {e}")
                return data  # Return original dict if model creation fails
        return data

    @staticmethod
    def serialize_arguments(inputs_dict: dict) -> dict:
        """Serialize Input objects to serializable values."""
        arguments = {}
        if inputs_dict:
            for key, value in inputs_dict.items():
                if hasattr(value, 'root') and hasattr(value.root, 'path'):
                    # Handle file/directory inputs
                    arguments[key] = str(value.root.path)
                elif hasattr(value, 'model_dump'):
                    # Handle Pydantic models
                    arguments[key] = value.model_dump()
                else:
                    # Handle other types
                    arguments[key] = str(value)
        return arguments

    @staticmethod
    def create_chat_message_from_record(record) -> 'ChatMessage':
        """Create ChatMessage from database record."""
        role = getattr(record, 'role', 'unknown')
        content = getattr(record, 'content', '')
        message = ChatMessage(role, content)
        message.id = getattr(record, 'message_id', None)

        # For tool_call messages, set meaningful content if empty
        if role == 'tool_call' and not content and hasattr(record, 'tool_calls') and record.tool_calls:
            tool_call = record.tool_calls[0] if record.tool_calls else {}
            endpoint = tool_call.get('name', 'unknown')
            content = f"🔧 Tool Call: {endpoint}"
            message.content = content

        # Set timestamp if available
        if hasattr(record, 'timestamp') and record.timestamp:
            message.timestamp = datetime.fromisoformat(str(record.timestamp).replace('Z', '+00:00'))
        # Preserve metadata (e.g., job_id) if present on the record
        if hasattr(record, 'metadata') and record.metadata:
            try:
                message.metadata = record.metadata
            except Exception:
                message.metadata = record.metadata

        return message

    @staticmethod
    def get_message_type(record) -> str:
        """Extract message type from record."""
        if hasattr(record, 'message_type'):
            return record.message_type
        elif isinstance(record, dict):
            return record.get('message_type', 'text')
        return 'text'

    @staticmethod
    def convert_record_to_message(record):
        """Convert dict or object to ChatMessageRecord."""
        if isinstance(record, dict):
            return ChatMessageRecord(**record)
        return record

    @staticmethod
    def render_message_in_chat(container, message, message_type: str = 'text', tool_calls=None,
                             endpoint: str = None, arguments: dict = None, result_content: str = None,
                             on_rerun_tool=None):
        """Render a message in the chat container with appropriate formatting."""
        # Prettify argument paths for display (convert Windows backslashes to POSIX style)
        def _prettify_value(v):
            # Recursively convert dict/list contents
            if isinstance(v, dict):
                return {k: _prettify_value(val) for k, val in v.items()}
            if isinstance(v, list):
                return [_prettify_value(i) for i in v]
            if isinstance(v, str):
                # If looks like a Windows path (contains backslashes or drive letter), normalize to native style
                try:
                    if '\\' in v or (len(v) > 1 and v[1] == ':'):
                        p = Path(v)
                        return p.as_posix()
                except Exception:
                    pass
                return v
            return v

        if arguments:
            try:
                arguments = _prettify_value(arguments)
            except (TypeError, ValueError):
                # best-effort; keep original if prettify fails
                pass

        if message_type == 'tool_call' and tool_calls:
            # Use extracted ToolCallCard component when available
            try:
                from frontend.components.chat.tool_call_card import render_tool_call_card
                # Prefer rendering arguments as a dict; render_tool_call_card will handle stringification
                logger.debug("render_message_in_chat: Rendering tool_call endpoint=%s container=%r arguments=%s result_content=%r", endpoint, container, arguments, result_content)
                render_tool_call_card(container, endpoint, arguments, result_content, on_rerun_tool, UIStyling)
            except Exception:
                # Render tool call with result and re-run button (fallback)
                with container:
                    with ui.card().classes(UIStyling.CARD_TOOL_CALL):
                        ui.label(f"🔧 Model Call: {endpoint}").classes(UIStyling.LABEL_TOOL_CALL_TITLE)

                        # Show arguments if any
                        if arguments:
                            ui.label(f"Arguments: {arguments}").classes(UIStyling.LABEL_TOOL_CALL_ARGS)

                        # Show result if available
                        if result_content:
                            ui.label("✅ Result:").classes(UIStyling.LABEL_TOOL_RESULT_TITLE)
                            ui.label(result_content).classes(UIStyling.LABEL_TOOL_RESULT_CONTENT)

                        # Add re-run button
                        if on_rerun_tool:
                            async def rerun_click():
                                logger.debug("message_service: rerun_click invoked for endpoint=%s arguments=%r", endpoint, arguments)
                                await on_rerun_tool(endpoint, arguments)

                            ui.button('Re-run Model', on_click=rerun_click).classes(UIStyling.BUTTON_RERUN_TOOL)

        elif message_type == 'tool_result':
            # Render standalone tool result (use component when available)
            try:
                from frontend.components.chat.tool_result_card import render_tool_result_card
                job_id = getattr(message, 'metadata', {}) and message.metadata.get('job_id')
                # Render tool result card; let it include the inline View Job button if job_id present
                render_tool_result_card(container, message.content, UIStyling, job_id=job_id)
            except Exception:
                with container:
                    with ui.card().classes(UIStyling.CARD_TOOL_RESULT):
                        ui.label("✅ Result").classes(UIStyling.LABEL_TOOL_RESULT_TITLE)
                        ui.label(message.content).classes(UIStyling.LABEL_TOOL_RESULT_CONTENT)

        elif message_type == 'error':
            # Render error message
            with container:
                with ui.card().classes(UIStyling.CARD_ERROR):
                    ui.label("❌ Error").classes(UIStyling.LABEL_ERROR_TITLE)
                    ui.label(message.content).classes(UIStyling.LABEL_ERROR_CONTENT)

        else:
            # Regular text message - delegate to existing render_message
            render_message(container, message)
