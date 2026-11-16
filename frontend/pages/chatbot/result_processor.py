from __future__ import annotations

import logging
from typing import Any

from frontend.chatbot.config import ToolRegistry
from frontend.components.chat import show_help_dialog
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.pages.chatbot.form_submit_handler import FormSubmitHandler
from frontend.pages.chatbot.pickers import AnalysisPicker, ToolPicker
from frontend.pages.chatbot.state import ChatbotStateManager, ChatMessage
from frontend.pages.chatbot.ui_delegate import ChatUIDelegate
from frontend.pages.chatbot.ui_flow import (
    load_and_show_form,
    show_tool_selection,
)
from frontend.utils import notify_info

logger = logging.getLogger(__name__)


class ResultProcessor:
    """Processes handler results and coordinates next actions."""

    def __init__(
        self,
        state_manager: ChatbotStateManager,
        tool_registry: ToolRegistry | None = None,
        form_submit_handler: FormSubmitHandler | None = None,
    ):
        self.state_manager = state_manager
        self.tool_registry = tool_registry
        self.form_submit_handler = form_submit_handler

    async def process_result(
        self,
        result: dict[str, Any],
        container: Any,
        core: Any,
        ui_delegate: ChatUIDelegate,
    ) -> None:
        """Process a handler result using the provided UI delegate."""
        result_type = result.get("type", "unknown")

        def _set_input(enabled: bool) -> None:
            try:
                ui_delegate.set_input_enabled(enabled)
            except Exception:
                pass
            if self.state_manager:
                self.state_manager.set_input_enabled(enabled)

        try:
            has_load_form = hasattr(ui_delegate, "load_form") and callable(
                getattr(ui_delegate, "load_form", None)
            )
            if result_type == "show_form":
                _set_input(False)
                endpoint = result.get("endpoint")
                arguments = result.get("arguments", {})
                if has_load_form:
                    await ui_delegate.load_form(endpoint, arguments)
                else:

                    def _on_cancel():
                        if self.state_manager:
                            self.state_manager.set_input_enabled(True)

                    submit_handler = self.form_submit_handler or FormSubmitHandler(
                        self.state_manager
                    )
                    await load_and_show_form(
                        container,
                        core,
                        endpoint,
                        arguments,
                        submit_handler,
                        on_form_cancel=_on_cancel,
                    )
                ui_delegate.update_status(
                    "Fill the Input form above and click Submit Job",
                    scroll_after=False,
                    scroll_to_form=True,
                )
            elif result_type == "multi_tool_calls":
                _set_input(False)
                tool_calls = result.get("tool_calls", [])
                notify_info(
                    f"Processing {len(tool_calls)} tool call(s) sequentially..."
                )
                if tool_calls and has_load_form:
                    first_call = tool_calls[0]
                    await ui_delegate.load_form(
                        first_call["endpoint"],
                        first_call["arguments"],
                        remaining_calls=tool_calls[1:] if len(tool_calls) > 1 else None,
                    )
                ui_delegate.update_status(
                    "Fill the Input form above and click Submit Job",
                    scroll_after=False,
                    scroll_to_form=True,
                )
            elif result_type == "message":
                _set_input(True)
                message = ChatMessage("assistant", result.get("content", ""))
                ui_delegate.add_message(message)
                ui_delegate.update_status("Rescuebox waiting for user..")
            elif result_type == "error":
                _set_input(True)
                await ui_delegate.show_error(result.get("content", "Unknown error"))
                ui_delegate.update_status("Ready")
            elif result_type == "help":
                _set_input(True)
                show_help_dialog(
                    result.get("content", "No help available"),
                    title="RescueBox Model Assistant Help",
                )
                ui_delegate.update_status("Ready")
            elif result_type == "tool_picker":
                _set_input(False)
                if container:
                    container.clear()
                picker = ToolPicker(container, self.tool_registry)
                ui_delegate.update_status(
                    "Select a tool from the menu above", scroll_after=False
                )
                endpoint, _ = await picker.select_tool()
                await show_tool_selection(container, endpoint)
            elif result_type == "analysis_picker":
                _set_input(False)
                if container:
                    container.clear()
                picker = AnalysisPicker(container)
                ui_delegate.update_status(
                    "Choose an option from the menu above", scroll_after=False
                )
                analysis_type = await picker.select_analysis()
                message = ChatMessage(
                    "assistant", f"Selected analysis: {analysis_type}"
                )
                ui_delegate.add_message(message)
            else:
                _set_input(True)
                await ui_delegate.show_error(f"Unknown response type: {result_type}")
                ui_delegate.update_status("Ready")

        except UI_RENDER_ERRORS as e:
            logger.error("Error processing result: %s", str(e))
            await ui_delegate.show_error(f"Error processing response: {e!s}")
