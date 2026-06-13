"""Chatbot page layout: header, modes, tool picker, form staging."""

from __future__ import annotations

import asyncio
import logging

from nicegui import ui

from frontend.chatbot.pipeline_context import get_pipeline_output_path
from frontend.components.chat import (
    UIOperations,
    create_chat_window,
    create_input_area,
    render_welcome_message,
    show_history_dialog,
)
from frontend.constants import UI_TITLES
from frontend.database import get_job_db
from frontend.design_tokens import Design
from frontend.pages.chatbot.pickers import ToolPicker
from frontend.pages.chatbot.storage_reads import read_pipeline_job_id
from frontend.pages.chatbot.ui_flow import load_and_show_form
from frontend.utils import app
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)

# Aliases for patching in tests (see ``frontend.pages.chatbot.ui``).
row = ui.row
column = ui.column
card = ui.card


class FormConfig:
    """Configuration and styling constants for chatbot forms."""

    FORM_REVEAL_OUTER_CLASSES = "w-full space-y-4 opacity-0 transition-opacity duration-300 rb-form-reveal-outer"
    FORM_SCROLL_AFTER_REVEAL_DELAY_S = 0.35

    @classmethod
    def reveal_outer_classes(cls) -> str:
        """CSS classes for the form reveal wrapper."""
        return cls.FORM_REVEAL_OUTER_CLASSES

    @classmethod
    def scroll_after_reveal_delay(cls) -> float:
        """Seconds to wait after form reveal before scrolling."""
        return cls.FORM_SCROLL_AFTER_REVEAL_DELAY_S


class ChatUIBuilder:
    def __init__(
        self,
        on_send,
        on_new_conversation,
        on_conversation_select,
        on_rerun_tool,
        tool_registry,
        core,
        form_submit_handler,
        status_text_ref=None,
        state_manager=None,
    ):
        self.on_send = on_send
        self.on_new_conversation = on_new_conversation
        self.on_conversation_select = on_conversation_select
        self.on_rerun_tool = on_rerun_tool
        self.tool_registry = tool_registry
        self.core = core
        self.form_submit_handler = form_submit_handler
        self.status_text_ref = status_text_ref
        self.state_manager = state_manager
        self.models_btn = None
        self.analyze_btn = None
        self.history_btn = None
        self.active_form = None
        self.mode_indicator = None
        self.input_area = None
        self.input_field = None
        self.chat_container = None

    def build_ui(self):
        pipeline_job_id = read_pipeline_job_id()
        with column().classes(
            "rb-chat-layout-core min-h-screen w-full flex flex-col bg-slate-50 relative"
        ):
            # We integrate the buttons directly into the card header below.
            with column().classes(
                "container mx-auto w-full max-w-6xl px-4 sm:px-8 py-8 flex-1 flex flex-col min-h-0 pb-16"
            ):
                # Page Header (Matches Jobs, Logs, Models pages)
                with row().classes("items-center gap-2 mb-6"):
                    ui.label(UI_TITLES.get("chatbot", "RescueBox Assistant")).classes(
                        "text-4xl font-bold text-slate-800"
                    )

                if pipeline_job_id:
                    output_path = get_pipeline_output_path(pipeline_job_id) or "N/A"
                    job = get_job_db().get_job_by_uid_sync(pipeline_job_id)
                    if job:
                        endpoint = job.endpoint or "Unknown"
                        pname = job.plugin_name or endpoint

                        with row().classes(
                            "w-full bg-rose-50 border border-rose-200 p-3 rounded-xl "
                            "items-center justify-between mb-4 shadow-sm"
                        ):
                            with row().classes("items-center gap-2"):
                                ui.icon("link").classes("text-[#881c1c]")
                                with column().classes("gap-0.5"):
                                    ui.label(
                                        f"Pipelining from Job {pipeline_job_id} ({pname})"
                                    ).classes("font-bold text-rose-900 text-sm")
                                    ui.label(f"Output Path: {output_path}").classes(
                                        "font-mono text-xs text-rose-700"
                                    )

                            def _clear_pipeline():
                                app.storage.user.pop("pipeline_job_id", None)
                                ui.notify("Pipeline cleared.", type="info")

                                def _reload_page() -> None:
                                    ui.navigate.reload()

                                ui.timer(0.1, _reload_page, once=True)

                            ui.button(
                                "Clear Pipeline", on_click=_clear_pipeline
                            ).classes(
                                "bg-red-50 hover:bg-red-100 text-[#881c1c] px-3 py-1 rounded text-xs transition-colors"
                            )

                with card().classes(Design.PANEL_SHELL_CHAT_CARD):
                    with row().classes(Design.PANEL_SHELL_HEADER):
                        with row().classes("items-center gap-3"):
                            ui.label("Active Mode:").classes(
                                "text-base font-bold text-slate-700"
                            )
                            self.mode_indicator = ui.badge(
                                "Chat mode", color=None
                            ).classes(
                                "text-sm font-semibold rb-chat-mode-badge px-3 py-1 rounded-full"
                            )

                        with row().classes("items-center gap-2"):
                            self.analyze_btn = (
                                ui.button("Chat", color=None)
                                .classes(
                                    "rb-chatbot-tab-btn px-4 py-2 rounded-lg font-semibold transition-all text-base"
                                )
                                .props("unelevated no-caps")
                            )
                            self.models_btn = (
                                ui.button("Menu", color=None)
                                .classes(
                                    "rb-chatbot-tab-btn px-4 py-2 rounded-lg font-semibold transition-all text-base"
                                )
                                .props("unelevated no-caps")
                            )
                            self.history_btn = (
                                ui.button(
                                    "History",
                                    color=None,
                                    on_click=self._show_history_dialog,
                                )
                                .classes(
                                    "rb-chatbot-tab-btn px-4 py-2 rounded-lg font-semibold transition-all text-base"
                                )
                                .props("unelevated no-caps")
                            )

                    chat_container = create_chat_window()
                    self.input_area = create_input_area(
                        self.status_text_ref, self.on_send
                    )
                    self.input_field = self.input_area.input_field

                below_input_area = column().classes(
                    "rb-chat-below-input-area w-full max-w-none space-y-4 mt-2 mb-4"
                )

            self._setup_mode_handlers(chat_container)

        self.chat_container = chat_container
        return (
            chat_container,
            self.input_field,
            self.status_text_ref,
            self.input_area,
            below_input_area,
        )

    def _setup_mode_handlers(self, chat_container):
        # Initial active state: Chat mode
        self.analyze_btn.classes("rb-tab-active")

        async def handle_models_click():
            self.mode_indicator.set_text("Menu mode")
            self.models_btn.classes("rb-tab-active")
            self.analyze_btn.classes(remove="rb-tab-active")
            chat_container.clear()

            # Hide the chat input area completely in Menu Mode
            if hasattr(self, "input_area") and self.input_area:
                self.input_area.classes("hidden")

            await asyncio.sleep(0.01)  # Give NiceGUI a moment
            picker = ToolPicker(
                chat_container, self.tool_registry, self._on_tool_selected
            )
            await picker.show()

        async def handle_analyze_click():
            self.mode_indicator.set_text("Chat mode")
            self.analyze_btn.classes("rb-tab-active")
            self.models_btn.classes(remove="rb-tab-active")
            chat_container.clear()

            # Show and enable the chat input area in Chat Mode
            if hasattr(self, "input_area") and self.input_area:
                self.input_area.classes(remove="hidden")
                if self.state_manager:
                    self.state_manager.set_input_enabled(True)

            render_welcome_message(chat_container)

        self.models_btn.on_click(handle_models_click)
        self.analyze_btn.on_click(handle_analyze_click)

    async def _on_tool_selected(self, endpoint, arguments):
        # Delete previous unsubmitted form if it exists
        if hasattr(self, "active_form") and self.active_form:
            try:
                self.active_form.delete()
            except UI_RENDER_ERRORS:
                pass
            self.active_form = None

        async def handle_form_submit(
            request_body, endpoint=None, task_schema=None, **kwargs
        ):
            # Form is being submitted, so it's no longer an active unsubmitted form
            if hasattr(self, "active_form"):
                self.active_form = None
            return await self.form_submit_handler.submit_form(
                request_body,
                endpoint,
                task_schema,
                self.chat_container,
                self.core,
                **kwargs,
            )

        def _on_cancel():
            if self.state_manager:
                self.state_manager.set_input_enabled(True)
            if hasattr(self, "active_form") and self.active_form:
                form_to_delete = self.active_form
                self.active_form = None

                def _delete_form() -> None:
                    form_to_delete.delete()

                ui.timer(0.01, _delete_form, once=True)

        # Stage 1: Grey out input area while form is being filled
        if self.state_manager:
            self.state_manager.set_input_enabled(False, hide_completely=False)

        self.active_form = await load_and_show_form(
            self.chat_container,
            self.core,
            endpoint,
            arguments or {},
            handle_form_submit,
            on_form_cancel=_on_cancel,
        )
        UIOperations.scroll_form_into_view_with_retries()

    def clear_active_form(self) -> None:
        """Remove any staged form card from the chat UI."""
        if self.active_form and hasattr(self.active_form, "delete"):
            try:
                self.active_form.delete()
            except UI_RENDER_ERRORS:
                pass
        self.active_form = None

    async def _show_history_dialog(self):
        await show_history_dialog(
            on_conversation_select=self.on_conversation_select,
        )
