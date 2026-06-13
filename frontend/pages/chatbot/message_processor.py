from __future__ import annotations

import asyncio
import logging

from frontend.chatbot.message_handler import MessageHandler
from frontend.database.chat_history_db import get_chat_history_db
from frontend.pages.chatbot.database_service import DatabaseService
from frontend.pages.chatbot.state import ChatbotStateManager, ChatMessage
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Handles message sending and processing for the chatbot."""

    def __init__(
        self, state_manager: ChatbotStateManager, message_handler: MessageHandler
    ):
        self.state_manager = state_manager
        self.message_handler = message_handler

    def is_processing(self) -> bool:
        """Whether a message send is in progress."""
        return self.state_manager.is_processing

    async def send_message(
        self,
        message_text,
        add_message_callback,
        process_result_callback,
        show_error_callback,
        update_status_callback,
    ):
        try:
            self.state_manager.set_processing(True)
            self.state_manager.set_input_enabled(False)
            await asyncio.sleep(0)
            update_status_callback("Processing message...")
            logger.info("send_message: %s ", message_text)
            await DatabaseService.ensure_active_conversation(self.state_manager)
            user_message = ChatMessage("user", message_text)
            add_message_callback(user_message)
            await asyncio.sleep(0)

            if self.state_manager.conversation_id:
                chat_history = get_chat_history_db()
                logger.info("add_message: %s ", message_text)
                await chat_history.add_message(
                    conversation_id=self.state_manager.conversation_id,
                    role="user",
                    content=message_text,
                )

            result = await self.message_handler.handle_message(
                message_text, update_status_callback
            )

            if result and result.get("type") == "message":
                content = result.get("content", "")
                message = ChatMessage("assistant", content)
                add_message_callback(message)
                self.state_manager.set_processing(False)
                self.state_manager.clear_input()
                await asyncio.sleep(0.5)
                self.state_manager.set_input_enabled(True)
                update_status_callback("Rescuebox waiting for user..")
                return None
            if result:
                self.state_manager.set_processing(False)
                await process_result_callback(result)
                self.state_manager.clear_input()
                result_type = result.get("type", "")
                if result_type in (
                    "tool_picker",
                    "analysis_picker",
                    "show_form",
                    "multi_tool_calls",
                ):
                    self.state_manager.set_input_enabled(False)
                else:
                    self.state_manager.set_input_enabled(True)

                if result_type == "tool_picker":
                    update_status_callback(
                        "Select a tool from the menu above", scroll_after=False
                    )
                elif result_type == "analysis_picker":
                    update_status_callback(
                        "Choose an option from the menu above", scroll_after=False
                    )
                elif result_type in ("show_form", "multi_tool_calls"):
                    update_status_callback(
                        "Fill the Input form above and click Submit Job",
                        scroll_to_form=True,
                    )
                else:
                    update_status_callback("Ready")
                return None

            self.state_manager.clear_input()
            self.state_manager.set_processing(False)
            self.state_manager.set_input_enabled(True)
            update_status_callback("Rescuebox waiting for user..")
            return result
        except UI_RENDER_ERRORS as e:
            logger.error("Error sending message: %s", str(e))
            self.state_manager.set_processing(False)
            show_error_callback(f"Failed to send message: {str(e)}")
            return None
