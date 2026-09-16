from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from nicegui import ui

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.pages.chatbot.form_submit_handler import FormSubmitHandler
from frontend.pages.chatbot.message_processor import MessageProcessor
from frontend.pages.chatbot.result_processor import ResultProcessor
from frontend.pages.chatbot.state import ChatbotStateManager

logger = logging.getLogger(__name__)


class MessageFlowCoordinator:
    """Unified coordinator for all chatbot message processing workflows."""

    def __init__(
        self, state_manager: ChatbotStateManager, form_loader: Callable | None = None
    ):
        self.state_manager = state_manager
        self.form_loader = form_loader
        self.logger = logging.getLogger(__name__)

        self.form_submit_handler = FormSubmitHandler(state_manager)
        self.message_processor = MessageProcessor(state_manager, None)
        self.result_processor = ResultProcessor(
            state_manager, None, form_submit_handler=self.form_submit_handler
        )

        self.logger.debug("MessageFlowCoordinator initialized")

    def set_message_handler(self, message_handler):
        self.message_processor.message_handler = message_handler

    def set_tool_registry(self, tool_registry):
        self.result_processor.tool_registry = tool_registry

    async def process_user_message(
        self,
        message_text: str,
        input_field: ui.textarea,
        is_processing_ref: dict,
        add_message_func: Callable,
        show_error_func: Callable,
        update_status_func: Callable,
        core: Any | None = None,
    ) -> None:
        try:
            self.logger.info("Starting user message processing flow")
            result = await self.message_processor.send_message(
                message_text=message_text,
                add_message_callback=add_message_func,
                process_result_callback=self._create_result_processor(
                    input_field,
                    is_processing_ref,
                    add_message_func,
                    show_error_func,
                    update_status_func,
                    core,
                ),
                show_error_callback=show_error_func,
                update_status_callback=update_status_func,
            )

            if result:
                await self._route_message_result(
                    result=result,
                    input_field=input_field,
                    is_processing_ref=is_processing_ref,
                    add_message_func=add_message_func,
                    show_error_func=show_error_func,
                    update_status_func=update_status_func,
                )
        except UI_RENDER_ERRORS as e:
            self.logger.error("Error in message processing flow: %s", str(e))
            await show_error_func(f"Message processing failed: {e!s}")

    def _create_result_processor(
        self,
        input_field,
        is_processing_ref,
        add_message_func,
        show_error_func,
        update_status_func,
        core,
    ):
        async def process_result(result: dict[str, Any]) -> None:
            await self._route_message_result(
                result=result,
                input_field=input_field,
                is_processing_ref=is_processing_ref,
                add_message_func=add_message_func,
                show_error_func=show_error_func,
                update_status_func=update_status_func,
                core=core,
            )
            is_processing_ref["value"] = False
            self.state_manager.set_processing(False)

        return process_result

    async def _route_message_result(
        self,
        result,
        input_field,
        is_processing_ref,
        add_message_func,
        show_error_func,
        update_status_func,
        core=None,
    ):
        callbacks = self._create_result_callbacks(
            input_field,
            is_processing_ref,
            add_message_func,
            show_error_func,
            update_status_func,
        )
        coordinator_chat_container = getattr(self, "chat_container", None)
        container_for_processing = coordinator_chat_container or input_field
        await self.result_processor.process_result(
            result=result, container=container_for_processing, core=core, **callbacks
        )

    def _create_result_callbacks(
        self,
        _input_field,
        _is_processing_ref,
        add_message_func,
        show_error_func,
        update_status_func,
    ) -> dict[str, Callable]:
        def add_assistant_message_func(message, scroll_after=True):
            add_message_func(message, scroll_after)

        async def load_and_show_form_func(
            endpoint: str, arguments: dict, remaining_calls=None
        ):
            if self.form_loader:
                await self.form_loader(endpoint, arguments, remaining_calls)

        return {
            "add_message_callback": add_assistant_message_func,
            "load_form_callback": load_and_show_form_func,
            "show_error_callback": show_error_func,
            "update_status_callback": update_status_func,
        }
