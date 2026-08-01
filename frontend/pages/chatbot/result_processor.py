from __future__ import annotations

import logging

from frontend.chatbot.config import ToolRegistry
from frontend.components.chat import show_help_dialog
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.pages.chatbot.form_submit_handler import FormSubmitHandler
from frontend.pages.chatbot.state import ChatbotStateManager, ChatMessage
from frontend.pages.chatbot.ui_flow import (
    load_and_show_form,
    show_analysis_picker,
    show_tool_picker,
    show_tool_selection,
)
from frontend.utils import notify_info

logger = logging.getLogger(__name__)


class ResultProcessor:
    """Processes handler results and coordinates next actions."""

    def __init__(
        self,
        state_manager: ChatbotStateManager,
        tool_registry: ToolRegistry,
        form_submit_handler: FormSubmitHandler | None = None,
    ):
        self.state_manager = state_manager
        self.tool_registry = tool_registry
        self.form_submit_handler = form_submit_handler

    def tool_registry_ref(self) -> ToolRegistry:
        """Tool registry used for picker and form flows."""
        return self.tool_registry

    async def process_result(
        self,
        result,
        container,
        core,
        add_message_callback,
        show_error_callback,
        update_status_callback,
        load_form_callback=None,
        set_input_enabled_callback=None,
    ):
        result_type = result.get("type", "unknown")

        def _set_input(enabled: bool):
            if set_input_enabled_callback:
                try:
                    set_input_enabled_callback(enabled)
                except UI_RENDER_ERRORS:
                    pass

        try:
            if result_type == "show_form":
                _set_input(False)
                endpoint = result.get("endpoint")
                arguments = result.get("arguments", {})
                if load_form_callback:
                    await load_form_callback(endpoint, arguments)
                else:

                    def _on_cancel():
                        if self.state_manager:
                            self.state_manager.set_input_enabled(True)

                    await load_and_show_form(
                        container,
                        core,
                        endpoint,
                        arguments,
                        self._create_form_submit_handler(container, core),
                        on_form_cancel=_on_cancel,
                    )
                update_status_callback("Ready", scroll_after=False)
            elif result_type == "multi_tool_calls":
                _set_input(False)
                tool_calls = result.get("tool_calls", [])
                notify_info(
                    f"Processing {len(tool_calls)} tool call(s) sequentially..."
                )
                if tool_calls and load_form_callback:
                    first_call = tool_calls[0]
                    await load_form_callback(
                        first_call["endpoint"],
                        first_call["arguments"],
                        remaining_calls=tool_calls[1:] if len(tool_calls) > 1 else None,
                    )
            elif result_type == "message":
                _set_input(True)
                message = ChatMessage("assistant", result.get("content", ""))
                add_message_callback(message)
            elif result_type == "error":
                _set_input(True)
                show_error_callback(result.get("content", "Unknown error"))
            elif result_type == "help":
                _set_input(True)
                show_help_dialog(
                    result.get("content", "No help available"),
                    title="RescueBox Model Assistant Help",
                )
            elif result_type == "tool_picker":
                _set_input(False)
                container.clear()
                await show_tool_picker(
                    container,
                    self.tool_registry,
                    self._create_tool_selected_handler(container),
                )
                update_status_callback("Ready", scroll_after=False)
            elif result_type == "analysis_picker":
                _set_input(False)
                container.clear()
                await show_analysis_picker(
                    container,
                    self._create_analysis_selected_handler(add_message_callback),
                )
                update_status_callback("Ready", scroll_after=False)
            else:
                _set_input(True)
                show_error_callback(f"Unknown response type: {result_type}")

            update_status_callback("Ready", scroll_to_form=False)
        except UI_RENDER_ERRORS as e:
            logger.error("Error processing result: %s", str(e))
            show_error_callback(f"Error processing response: {e!s}")

    def _create_form_submit_handler(self, container, core):
        async def form_submit_handler(
            request_body, endpoint=None, task_schema=None, **kwargs
        ):
            handler = self.form_submit_handler or FormSubmitHandler(self.state_manager)
            return await handler.submit_form(
                request_body,
                endpoint or kwargs.get("endpoint"),
                task_schema,
                container,
                core,
            )

        return form_submit_handler

    def _create_tool_selected_handler(self, container):
        async def tool_selected_handler(endpoint):
            await show_tool_selection(container, endpoint)

        return tool_selected_handler

    def _create_analysis_selected_handler(self, add_message_callback):
        async def analysis_selected_handler(analysis_type):
            message = ChatMessage("assistant", f"Selected analysis: {analysis_type}")
            add_message_callback(message)

        return analysis_selected_handler
