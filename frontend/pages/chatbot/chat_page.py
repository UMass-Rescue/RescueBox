"""Chatbot page controller."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from frontend.chatbot.config import ChatbotConfig, ToolRegistry
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.message_handler import MessageHandler
from frontend.components.chat import (
    UIOperations,
    get_latest_input_area,
    render_welcome_message,
)
from frontend.database import get_chat_history_db, get_job_db
from frontend.pages.chatbot.conversation_restore import restore_conversation
from frontend.pages.chatbot.database_service import DatabaseService
from frontend.pages.chatbot.message_flow_coordinator import MessageFlowCoordinator
from frontend.pages.chatbot.history_ui import render_message
from frontend.pages.chatbot.state import ChatbotStateManager, ChatMessage
from frontend.pages.chatbot.ui_builder import ChatUIBuilder
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.pages.chatbot.ui_flow import (
    load_and_show_form,
    show_error_message,
    show_results,
)

logger = logging.getLogger(__name__)


class ChatbotPage:
    _instance = None

    @classmethod
    def get_instance(cls):
        return cls._instance

    def __init__(self, config: Optional[ChatbotConfig] = None):
        ChatbotPage._instance = self
        self.config = config or ChatbotConfig()
        self.core = ChatbotCore(self.config)
        self.message_handler = MessageHandler(self.core, self.config)
        self.tool_registry = ToolRegistry()
        self.state_manager = ChatbotStateManager()

        self.message_flow_coordinator = MessageFlowCoordinator(
            self.state_manager, self.load_and_show_form
        )
        self.message_flow_coordinator.set_message_handler(self.message_handler)
        self.message_flow_coordinator.set_tool_registry(self.tool_registry)

        self.form_handler = self.message_flow_coordinator.form_submit_handler
        self.chat_container = None
        self.input_field = None

    async def handle_conversation_select(self, conversation_id: str) -> None:
        """Load a conversation from history (public entry for routes)."""
        await self._handle_conversation_select(conversation_id)

    async def handle_rerun_tool(self, message_id: str) -> None:
        """Re-run a tool from a stored message (public entry for routes)."""
        await self._handle_rerun_tool(message_id)

    @property
    def conversation_id(self) -> Optional[str]:
        return self.state_manager.conversation_id

    async def new_conversation(self) -> str:
        """Start a new persisted conversation (state, storage, and DB row)."""
        self.state_manager.reset_conversation()
        if getattr(self, "chat_container", None):
            self.chat_container.clear()
            render_welcome_message(self.chat_container)
        self.state_manager.set_input_enabled(True)
        return await DatabaseService.ensure_active_conversation(self.state_manager)

    async def render(self):
        builder = ChatUIBuilder(
            on_send=self._handle_send_message,
            on_new_conversation=self._handle_new_conversation,
            on_conversation_select=self._handle_conversation_select,
            on_rerun_tool=self._handle_rerun_tool,
            tool_registry=self.tool_registry,
            core=self.core,
            form_submit_handler=self.form_handler,
            status_text_ref=self.state_manager,
            state_manager=self.state_manager,
        )
        self.chat_container, self.input_field, _, input_area, _ = builder.build_ui()
        self.message_flow_coordinator.chat_container = self.chat_container
        self.state_manager.set_input_area(input_area)
        self.state_manager.set_input_field(self.input_field)
        await DatabaseService.ensure_active_conversation(self.state_manager)

    async def _handle_send_message(self):
        msg = self.input_field.value.strip()
        if not msg:
            return
        await self.message_flow_coordinator.process_user_message(
            message_text=msg,
            input_field=self.input_field,
            is_processing_ref={"value": False},
            add_message_func=self._add_message,
            show_error_func=self._show_error,
            update_status_func=self._update_status,
            core=self.core,
        )

    def _add_message(self, message: ChatMessage, scroll_after: bool = True):
        self.state_manager.add_message(message)
        render_message(self.chat_container, message)
        if scroll_after:
            UIOperations.scroll_to_bottom()

    async def _show_error(self, error_message: str):
        show_error_message(self.chat_container, error_message)

    def _update_status(
        self, status: str, scroll_after: bool = True, scroll_to_form: bool = False
    ):
        self.state_manager.set_status(status)
        if scroll_after:
            if scroll_to_form:
                UIOperations.scroll_form_into_view_with_retries()
            else:
                UIOperations.scroll_to_bottom()

    async def _handle_new_conversation(self):
        await self.new_conversation()

    async def load_and_show_form(
        self, endpoint, arguments, remaining_calls=None, container=None
    ):
        target_container = container or self.chat_container

        async def _on_submit(
            request_body, endpoint=endpoint, task_schema=None, **kwargs
        ):
            return await self.form_handler.submit_form(
                request_body,
                endpoint,
                task_schema,
                target_container,
                self.core,
                remaining_calls=remaining_calls,
                **kwargs,
            )

        await load_and_show_form(
            target_container, self.core, endpoint, arguments, _on_submit
        )
        UIOperations.scroll_form_into_view_with_retries()

    async def _handle_conversation_select(self, conversation_id: str):
        await restore_conversation(
            self.state_manager, self.chat_container, conversation_id
        )

    async def load_conversation_from_data(self, conversation_data: dict):
        """Load conversation when ``conversation_id`` is present in a stash dict."""
        cid = conversation_data.get("conversation_id")
        if cid:
            await self._handle_conversation_select(cid)

    async def _poll_job_status(
        self, job_id: str, _endpoint: str, interval: float | None = None
    ):
        """Poll for job status updates and trigger result rendering."""
        if interval is None:
            interval = 2.0
        job_db = get_job_db()
        terminal = {"completed", "failed", "finished"}
        while True:
            job = await job_db.get_job_by_uid(job_id)
            if not job:
                break
            status = getattr(job, "status", "").lower()
            if status in terminal:
                if status in {"completed", "finished"}:
                    response = getattr(job, "response", None) or getattr(
                        job, "response_body", None
                    )
                    await show_results(self.chat_container, response, job_id)
                break
            await asyncio.sleep(interval)

    async def _handle_rerun_tool(self, message_id: str):
        """Handle re-running a tool from a specific message."""
        if not isinstance(message_id, str) or not message_id.strip():
            logger.warning("Ignoring invalid rerun message_id: %r", message_id)
            UIOperations.safe_notify(
                "Could not find tool metadata for this message.", type="warning"
            )
            return

        chat_db = get_chat_history_db()
        msg = await chat_db.get_tool_call_by_id(message_id)
        if not msg:
            UIOperations.safe_notify(
                "Could not find tool metadata for this message.", type="warning"
            )
            return

        # Prefer canonical tool_call_* fields written by DatabaseService.
        endpoint = getattr(msg, "tool_call_endpoint", None)
        arguments = getattr(msg, "tool_call_arguments", None) or {}

        # Backward-compat: older rows stored endpoint/arguments in metadata.
        if not endpoint and getattr(msg, "metadata", None):
            endpoint = msg.metadata.get("endpoint")
            arguments = msg.metadata.get("arguments", arguments)

        arguments = await self._resolve_rerun_arguments(msg, arguments)

        if endpoint:
            await self._re_run_tool(endpoint, arguments)
            return

        UIOperations.safe_notify(
            "Could not find tool metadata for this message.", type="warning"
        )

    async def _resolve_rerun_arguments(self, msg, arguments: dict) -> dict:
        """Fill inputs/parameters from the job record when history row omitted them."""
        has_payload = isinstance(arguments, dict) and (
            arguments.get("inputs") is not None
            or arguments.get("parameters") is not None
        )
        if has_payload:
            return arguments

        meta = getattr(msg, "metadata", None) or {}
        job_id = meta.get("job_id") if isinstance(meta, dict) else None
        if not job_id:
            return arguments

        job = await get_job_db().get_job_by_uid(job_id)
        if not job:
            return arguments

        snap = DatabaseService._job_request_snapshot(getattr(job, "request", None))
        return snap if snap else arguments

    async def _re_run_tool(self, endpoint: str, arguments: dict):
        """Re-run a tool with given endpoint and arguments."""
        logger.info("Re-running tool: %s", endpoint)
        UIOperations.safe_notify(f"Re-running: {endpoint}", type="info")
        try:
            container = get_latest_input_area() or self.chat_container
        except UI_RENDER_ERRORS:
            container = self.chat_container

        await self.load_and_show_form(endpoint, arguments, container=container)
