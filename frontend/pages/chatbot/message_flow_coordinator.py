from __future__ import annotations

import asyncio
import logging
from typing import Any
from nicegui import ui
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.database.chat_history_db import get_chat_history_db
from frontend.pages.chatbot.database_service import DatabaseService
from frontend.pages.chatbot.form_submit_handler import FormSubmitHandler
from frontend.pages.chatbot.result_processor import ResultProcessor
from frontend.pages.chatbot.state import ChatbotStateManager, ChatMessage
from frontend.pages.chatbot.ui_delegate import ChatUIDelegate

logger = logging.getLogger(__name__)


class MessageFlowCoordinator:
    """Unified coordinator for all chatbot message processing workflows."""

    def __init__(
        self,
        state_manager: ChatbotStateManager,
        ui_delegate: ChatUIDelegate | None = None,
        message_handler: Any | None = None,
        tool_registry: Any | None = None,
    ):
        self.state_manager = state_manager
        self.ui_delegate = ui_delegate
        self.message_handler = message_handler
        self.logger = logging.getLogger(__name__)

        self.form_submit_handler = FormSubmitHandler(state_manager)
        self.result_processor = ResultProcessor(
            state_manager, tool_registry, form_submit_handler=self.form_submit_handler
        )
        self.message_processor = self
        self.chat_container: ui.element | None = None

        self.logger.debug("MessageFlowCoordinator initialized")

    def is_processing(self) -> bool:
        """Whether a message send is in progress."""
        return self.state_manager.is_processing

    def set_message_handler(self, message_handler: Any) -> None:
        self.message_handler = message_handler
        if self.message_processor is not self and hasattr(self.message_processor, "message_handler"):
            self.message_processor.message_handler = message_handler

    def set_tool_registry(self, tool_registry: Any) -> None:
        self.result_processor.tool_registry = tool_registry

    async def send_message(
        self,
        message_text: str,
        ui_delegate: ChatUIDelegate,
    ) -> dict[str, Any] | None:
        """Send a user message, record it, and directly return the handler result dictionary."""
        try:
            self.state_manager.set_processing(True)
            self.state_manager.set_input_enabled(False)
            await asyncio.sleep(0)
            ui_delegate.update_status("Processing message...")
            self.logger.info("send_message: %s ", message_text)
            await DatabaseService.ensure_active_conversation(self.state_manager)
            user_message = ChatMessage("user", message_text)
            ui_delegate.add_message(user_message)
            await asyncio.sleep(0)

            if self.state_manager.conversation_id:
                chat_history = get_chat_history_db()
                self.logger.info("add_message: %s ", message_text)
                await chat_history.add_message(
                    conversation_id=self.state_manager.conversation_id,
                    role="user",
                    content=message_text,
                )

            status_updater = getattr(ui_delegate, "update_status", None)
            result = await self.message_handler.handle_message(
                message_text, status_updater
            )

            self.state_manager.clear_input()
            return result
        except UI_RENDER_ERRORS as e:
            self.logger.error("Error sending message: %s", str(e))
            self.state_manager.set_processing(False)
            await ui_delegate.show_error(f"Failed to send message: {e!s}")
            return None

    async def process_user_message(
        self,
        message_text: str,
        ui_delegate: ChatUIDelegate,
        core: Any | None = None,
    ) -> None:
        """Process user message using direct async return flow and UI delegate."""
        try:
            self.logger.info("Starting user message processing flow")
            sender = (
                self.message_processor.send_message
                if hasattr(self, "message_processor") and self.message_processor is not self
                else self.send_message
            )
            result = await sender(
                message_text=message_text,
                ui_delegate=ui_delegate,
            )

            if result:
                await self._route_message_result(
                    result=result,
                    ui_delegate=ui_delegate,
                    core=core,
                )
        except UI_RENDER_ERRORS as e:
            self.logger.error("Error in message processing flow: %s", str(e))
            await ui_delegate.show_error(f"Message processing failed: {e!s}")
        finally:
            self.state_manager.set_processing(False)

    async def _route_message_result(
        self,
        result: dict[str, Any],
        ui_delegate: ChatUIDelegate,
        core: Any | None = None,
    ) -> None:
        """Route message result directly to result_processor using UI delegate."""
        coordinator_chat_container = getattr(self, "chat_container", None)
        await self.result_processor.process_result(
            result=result,
            container=coordinator_chat_container,
            core=core,
            ui_delegate=ui_delegate,
        )
