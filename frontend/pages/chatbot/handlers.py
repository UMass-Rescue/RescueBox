from __future__ import annotations
import logging
import asyncio
from typing import Any, Optional
from nicegui import ui

from frontend.utils import get_user_id_for_jobs
from .database_service import DatabaseService

logger = logging.getLogger(__name__)


class BaseHandler:
    """Base class for all handler classes providing common functionality."""

    def __init__(self, logger_name: Optional[str] = None):
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)


class JobSubmissionOrchestrator(BaseHandler):
    """Orchestrates job submission and progress tracking."""

    def __init__(self, form_handler: Any):
        super().__init__()
        self.form_handler = form_handler
        self.state_manager = getattr(form_handler, "state_manager", None)
        self.error_handler = FormErrorHandler()

    async def submit_job(
        self,
        request_body,
        endpoint,
        task_schema,
        container,
        core,
        remaining_calls=None,
        conversation_id=None,
        **kwargs,
    ):
        return await self._execute_job(
            request_body,
            endpoint,
            task_schema,
            container,
            core,
            remaining_calls,
            conversation_id,
            **kwargs,
        )

    async def _execute_job(
        self,
        request_body,
        endpoint,
        task_schema,
        container,
        core,
        remaining_calls=None,
        conversation_id=None,
        **kwargs,
    ):
        """Execute the job submission, optionally backgrounded."""
        from frontend.components.shared import render_loading_row
        from frontend.chatbot.config import ToolRegistry
        from frontend.pages.chatbot import background_tasks

        self.state_manager = self.form_handler.state_manager
        self.state_manager.set_processing(True)

        form_element = kwargs.get("form_element")
        target_container = form_element or container
        loading_row = None
        if target_container:
            with target_container:
                if form_element and hasattr(form_element, "clear"):
                    form_element.clear()
                loading_row = render_loading_row(
                    f"Processing {ToolRegistry.display_name_for_endpoint(endpoint)}..."
                )

        pipeline_total = (1 + len(remaining_calls)) if remaining_calls else None
        db_kwargs = {
            k: v for k, v in kwargs.items() if k not in ("form_element",)
        }

        # Create and track job in the main thread (so we get the job_id and can redirect immediately)
        job_id = None
        try:
            job_record = await DatabaseService.create_and_track_job(
                request_body,
                endpoint,
                task_schema,
                user_id=get_user_id_for_jobs(),
                pipeline_total_steps=pipeline_total,
                **db_kwargs,
            )
            job_id = job_record.get("job_id") if job_record else None
        except Exception as e:
            self.logger.error(f"Failed to create and track job in DB: {e}")

        if job_id:
            # Redirect immediately to the general jobs view so the user can see the list of jobs
            ui.timer(0.1, lambda: ui.navigate.to("/jobs"), once=True)

        async def do_submit():
            try:
                if conversation_id and job_id:
                    await DatabaseService.save_job_started_to_history(
                        conversation_id,
                        endpoint,
                        job_id,
                        request_body=request_body,
                    )

                response_body = await core.submit_job(request_body, endpoint)

                if job_id:
                    await DatabaseService.complete_job(job_id, response_body)

                if loading_row and hasattr(loading_row, "delete"):
                    try:
                        loading_row.delete()
                    except Exception:
                        pass

                try:
                    await self._handle_success(
                        request_body,
                        endpoint,
                        task_schema,
                        target_container,
                        core,
                        remaining_calls,
                        conversation_id,
                        response_body,
                        {"job_id": job_id},
                    )
                except Exception as ui_err:
                    self.logger.debug(f"UI update skipped (likely navigated away): {ui_err}")
            except Exception as e:
                self.logger.error(f"Job submission failed: {e}")
                message = str(e)
                if job_id:
                    try:
                        await DatabaseService.update_job_status(
                            job_uid=job_id, status="Failed", status_text=message
                        )
                    except Exception as db_err:
                        self.logger.error(f"Failed to update job status to Failed in DB: {db_err}")
                if conversation_id:
                    try:
                        await DatabaseService.save_error_to_history(
                            conversation_id, endpoint, message
                        )
                    except Exception as hist_err:
                        self.logger.error(f"Failed to save error to chat history: {hist_err}")
                if loading_row and hasattr(loading_row, "delete"):
                    try:
                        loading_row.delete()
                    except Exception:
                        pass
                
                try:
                    if "demo_???" in message:
                        from frontend.pages.chatbot.ui import UIOperations

                        UIOperations.safe_notify(message, type="warning")
                    else:
                        self.error_handler.display_error_boundary(
                            target_container, "Submission Failed", message
                        )
                except Exception as ui_err:
                    self.logger.debug(f"Could not display error to UI: {ui_err}")
            finally:
                try:
                    self.state_manager.set_processing(False)
                    self.state_manager.set_input_enabled(True)
                except Exception:
                    pass

        background_tasks.create(do_submit())
        return True

    async def _handle_success(
        self,
        _request_body,
        endpoint,
        task_schema,
        container,
        core,
        remaining_calls,
        conversation_id,
        response_body,
        job_info,
    ):
        from frontend.pages.chatbot.ui import show_results

        job_id = job_info.get("job_id")

        if conversation_id:
            await DatabaseService.save_tool_result_to_history(
                conversation_id, endpoint, job_id
            )

        await show_results(container, response_body, job_id)

        if remaining_calls:
            await self.handle_remaining_calls(
                remaining_calls,
                response_body,
                container,
                core,
                conversation_id=conversation_id,
                pipeline_root_job_id=job_id,
            )
        else:
            self.state_manager.set_processing(False)
            self.state_manager.set_input_enabled(True)

    async def handle_remaining_calls(
        self, remaining_calls, response_body, container, core, **kwargs
    ):
        from frontend.pages.chatbot.coordinator import PipelineHandler

        pipeline = PipelineHandler(self)
        await pipeline.handle_remaining_calls(
            remaining_calls, response_body, container, core, **kwargs
        )


class FormErrorHandler:
    def display_error_boundary(self, container, title: str, message: str):
        from frontend.pages.chatbot.ui import UIOperations
        from frontend.utils.ui import _safe_ui_call

        UIOperations.safe_notify(f"{title}: {message}", type="negative")

        def _add_label():
            with container:
                ui.label(f"Error: {message}").classes(
                    "p-4 bg-red-50 text-red-700 rounded border border-red-200"
                )

        _safe_ui_call(_add_label)


class ToolPicker(BaseHandler):
    def __init__(self, container, tool_registry, on_tool_selected):
        super().__init__()
        self.container = container
        self.tool_registry = tool_registry
        self.on_tool_selected = on_tool_selected

    async def show(self):
        from frontend.design_tokens import Design

        self.logger.info(
            f"ToolPicker.show started. Registry type: {type(self.tool_registry)}"
        )

        menu = getattr(self.tool_registry, "TOOL_MENU", {})
        if not menu:
            from frontend.chatbot.config import ToolRegistry

            menu = ToolRegistry.TOOL_MENU

        self.logger.info(
            f"ToolPicker.show menu source: {'Instance' if hasattr(self.tool_registry, 'TOOL_MENU') else 'Class'}. Items: {len(menu)}"
        )

        def get_tool_icon(name: str) -> str:
            name_lower = name.lower()
            if "transcribe" in name_lower or "audio" in name_lower:
                return "mic"
            if "describe" in name_lower or "summarize images" in name_lower:
                return "visibility"
            if "search images" in name_lower:
                return "image_search"
            if "age" in name_lower or "gender" in name_lower:
                return "face_retouching_natural"
            if "deepfake" in name_lower:
                return "security"
            if "upload face" in name_lower:
                return "cloud_upload"
            if "find face" in name_lower or "face match" in name_lower:
                return "person_search"
            if "summarize text" in name_lower or "text_summarization" in name_lower:
                return "summarize"
            if "search text" in name_lower:
                return "find_in_page"
            if "mount" in name_lower or "ufdr" in name_lower:
                return "folder_open"
            if "similar" in name_lower:
                return "photo_library"
            return "extension"

        with self.container:
            with ui.card().classes("w-full max-w-full bg-white border border-slate-200 shadow-md rounded-2xl overflow-hidden p-0"):
                with ui.row().classes(Design.PANEL_SHELL_HEADER):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("extension", size="sm").classes("text-[#881c1c]")
                        ui.label("RescueBox Plugin Selector").classes(
                            Design.PANEL_SHELL_HEADER_TITLE
                        )

                with ui.column().classes("p-6 gap-3 w-full bg-slate-50"):
                    ui.label("Choose a plugin to run:").classes(
                        "text-sm font-semibold text-slate-500 uppercase tracking-wider"
                    )
                    if not menu:
                        ui.label("No plugins available in TOOL_MENU.").classes(
                            "text-sm text-rose-500 font-medium"
                        )
                    else:
                        for num, tool in menu.items():
                            self.logger.info(
                                f"Adding tool to UI: {num} - {tool.get('name')}"
                            )
                            row = ui.row().classes(
                                "w-full min-w-0 py-4 px-5 rounded-xl border border-slate-200 bg-white shadow-sm "
                                "hover:bg-slate-50 hover:border-[#881c1c] cursor-pointer transition-all duration-150 "
                                "items-center justify-between gap-4 border-l-4 border-l-[#881c1c]"
                            )
                            row.on(
                                "click",
                                lambda *a, t=tool: self.on_tool_selected(
                                    t["endpoint"], {}
                                ),
                            )
                            with row:
                                # Left side: Icon and Text
                                with ui.row().classes("items-center gap-4 flex-1 min-w-0"):
                                    # Beautiful icon container
                                    with ui.element("div").classes(
                                        "w-12 h-12 rounded-xl bg-[#881c1c]/5 flex items-center justify-center shrink-0 border border-[#881c1c]/10"
                                    ):
                                        ui.icon(get_tool_icon(tool["name"]), size="24px").classes("text-[#881c1c]")
                                    
                                    # Text column
                                    with ui.column().classes("flex-1 min-w-0 gap-0.5"):
                                        ui.label(f'{num}. {tool["name"]}').classes(
                                            "text-lg font-bold text-slate-800 leading-snug"
                                        )
                                        ui.label(tool.get("desc", "No description")).classes(
                                            "text-sm sm:text-base text-slate-500 whitespace-normal break-words leading-relaxed"
                                        )
                                
                                # Right side: Launch action indicator
                                with ui.row().classes("items-center gap-1 shrink-0 text-[#881c1c] font-semibold text-sm bg-[#881c1c]/5 hover:bg-[#881c1c]/10 px-3 py-1.5 rounded-lg transition-all"):
                                    ui.label("Launch")
                                    ui.icon("arrow_forward", size="16px")

        self.logger.info("ToolPicker.show finished building UI.")


class AnalysisPicker(BaseHandler):
    def __init__(self, container, on_analysis_selected):
        super().__init__()
        self.container = container
        self.on_analysis_selected = on_analysis_selected

    async def show(self):
        from frontend.design_tokens import Design

        self.logger.info("AnalysisPicker.show started")
        with self.container:
            with ui.card().classes("w-full max-w-full bg-white border border-slate-200 shadow-md rounded-2xl overflow-hidden p-0"):
                with ui.row().classes(Design.PANEL_SHELL_HEADER):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("analytics", size="sm").classes("text-[#881c1c]")
                        ui.label("Analysis Mode").classes(Design.PANEL_SHELL_HEADER_TITLE)

                with ui.column().classes("p-6 gap-3 w-full bg-slate-50"):
                    ui.label("Select an analysis type:").classes(
                        "text-sm font-semibold text-slate-500 uppercase tracking-wider"
                    )
                    options = ["Surface Scan", "Deep Forensic", "AI Content Analysis"]
                    analysis_details = {
                        "Surface Scan": {
                            "desc": "Quickly analyze metadata, file headers, and basic structures",
                            "icon": "radar"
                        },
                        "Deep Forensic": {
                            "desc": "Comprehensive, byte-level analysis of all partitions and hidden data",
                            "icon": "biotech"
                        },
                        "AI Content Analysis": {
                            "desc": "Leverage machine learning models to detect objects, faces, and transcribe media",
                            "icon": "psychology"
                        }
                    }
                    for a_type in options:
                        details = analysis_details.get(a_type, {"desc": "Run automated analysis", "icon": "analytics"})
                        self.logger.info(f"Adding analysis option: {a_type}")
                        row = ui.row().classes(
                            "w-full min-w-0 py-4 px-5 rounded-xl border border-slate-200 bg-white shadow-sm "
                            "hover:bg-slate-50 hover:border-[#881c1c] cursor-pointer transition-all duration-150 "
                            "items-center justify-between gap-4 border-l-4 border-l-[#881c1c]"
                        )
                        row.on(
                            "click", lambda *a, t=a_type: self.on_analysis_selected(t)
                        )
                        with row:
                            # Left side: Icon and Text
                            with ui.row().classes("items-center gap-4 flex-1 min-w-0"):
                                # Beautiful icon container
                                with ui.element("div").classes(
                                    "w-12 h-12 rounded-xl bg-[#881c1c]/5 flex items-center justify-center shrink-0 border border-[#881c1c]/10"
                                ):
                                    ui.icon(details["icon"], size="24px").classes("text-[#881c1c]")
                                
                                # Text column
                                with ui.column().classes("flex-1 min-w-0 gap-0.5"):
                                    ui.label(a_type).classes(
                                        "text-lg font-bold text-slate-800 leading-snug"
                                    )
                                    ui.label(details["desc"]).classes(
                                        "text-sm sm:text-base text-slate-500 whitespace-normal break-words leading-relaxed"
                                    )
                            
                            # Right side: Launch action indicator
                            with ui.row().classes("items-center gap-1 shrink-0 text-[#881c1c] font-semibold text-sm bg-[#881c1c]/5 hover:bg-[#881c1c]/10 px-3 py-1.5 rounded-lg transition-all"):
                                ui.label("Analyze")
                                ui.icon("arrow_forward", size="16px")
        self.logger.info("AnalysisPicker.show finished building UI.")


def _compose_age_gender_pipeline_filter(gender, age_op, age_val):
    parts = []
    if gender:
        parts.append(f"Gender={gender}")
    if age_val is not None:
        sym = {"lt": "<", "lte": "<=", "eq": "=", "gt": ">", "gte": ">="}.get(
            age_op, "<"
        )
        parts.append(f"Age {sym} {age_val}")
    return ", ".join(parts)


async def show_case_notes_dialog() -> Optional[str]:
    from frontend.design_tokens import Design

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    with ui.dialog() as dialog, ui.card().classes(Design.PANEL_SHELL_CARD_NARROW):
        with ui.row().classes(Design.PANEL_SHELL_HEADER):
            with ui.row().classes("items-center gap-2"):
                ui.icon("rate_review", size="sm").classes("text-[#881c1c]")
                ui.label("Job Submission Details").classes(Design.PANEL_SHELL_HEADER_TITLE)
            ui.button(
                icon="close", color=None, on_click=lambda: (future.set_result(None), dialog.close())
            ).props("flat round dense").classes(Design.PANEL_SHELL_HEADER_ICON)

        with ui.column().classes(Design.PANEL_SHELL_BODY + " gap-4"):
            ui.label("Add optional notes for the case file:").classes(
                "text-sm text-slate-500 font-medium"
            )
            # Use rb-case-notes-field to ensure maroon/gray brand colors and no blue/indigo
            notes = (
                ui.textarea(label="Case Notes")
                .classes("w-full rb-case-notes-field")
                .props("outlined")
            )

        with ui.row().classes(Design.PANEL_SHELL_FOOTER + " justify-end"):
            ui.button(
                "Skip & Submit",
                color=None,
                on_click=lambda: (future.set_result(""), dialog.close()),
            ).classes(Design.BTN_MEDIUM_GRAY).props("outline")
            ui.button(
                "Submit with Notes",
                color=None,
                on_click=lambda: (future.set_result(notes.value), dialog.close()),
            ).classes(Design.BTN_PRIMARY)
    dialog.open()
    return await future
