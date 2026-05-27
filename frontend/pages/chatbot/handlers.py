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
        self.state_manager = getattr(form_handler, 'state_manager', None)
        self.error_handler = FormErrorHandler()

    async def submit_job(self, request_body, endpoint, task_schema, container, core, remaining_calls=None, conversation_id=None, **kwargs):
        return await self._execute_job(request_body, endpoint, task_schema, container, core, remaining_calls, conversation_id, **kwargs)

    async def _execute_job(self, request_body, endpoint, task_schema, container, core, remaining_calls=None, conversation_id=None, **kwargs):
        """Execute the job submission, optionally backgrounded."""
        from frontend.components.shared import render_loading_row
        from frontend.chatbot.config import ToolRegistry
        from frontend.pages.chatbot import background_tasks

        self.state_manager = self.form_handler.state_manager
        self.state_manager.set_processing(True)
        
        form_element = kwargs.get('form_element')
        target_container = form_element or container
        loading_row = None
        if target_container:
            with target_container:
                if form_element and hasattr(form_element, 'clear'): form_element.clear()
                loading_row = render_loading_row(f"Processing {ToolRegistry.display_name_for_endpoint(endpoint)}...")

        async def do_submit():
            try:
                pipeline_total = (1 + len(remaining_calls)) if remaining_calls else None
                db_kwargs = {k: v for k, v in kwargs.items() if k not in ('form_element',)}
                
                job_record = await DatabaseService.create_and_track_job(
                    request_body, endpoint, task_schema, 
                    user_id=get_user_id_for_jobs(),
                    pipeline_total_steps=pipeline_total,
                    **db_kwargs
                )
                job_id = job_record.get('job_id') if job_record else None

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

                if loading_row and hasattr(loading_row, 'delete'):
                    try: loading_row.delete()
                    except: pass
                
                await self._handle_success(request_body, endpoint, task_schema, target_container, core, remaining_calls, conversation_id, response_body, {'job_id': job_id})
            except Exception as e:
                self.logger.error(f"Job submission failed: {e}")
                if loading_row and hasattr(loading_row, 'delete'):
                    try: loading_row.delete()
                    except: pass
                message = str(e)
                if "demo_???" in message:
                    from frontend.pages.chatbot.ui import UIOperations
                    UIOperations.safe_notify(message, type="warning")
                else:
                    self.error_handler.display_error_boundary(target_container, "Submission Failed", message)
            finally:
                self.state_manager.set_processing(False)
                self.state_manager.set_input_enabled(True)
        
        background_tasks.create(do_submit())
        return True

    async def _handle_success(self, _request_body, endpoint, task_schema, container, core, remaining_calls, conversation_id, response_body, job_info):
        from frontend.pages.chatbot.ui import show_results
        job_id = job_info.get('job_id')
        
        if conversation_id:
            await DatabaseService.save_tool_result_to_history(conversation_id, endpoint, job_id)

        await show_results(container, response_body, job_id)
        
        if remaining_calls:
            await self.handle_remaining_calls(remaining_calls, response_body, container, core, conversation_id=conversation_id, pipeline_root_job_id=job_id)
        else:
            self.state_manager.set_processing(False)
            self.state_manager.set_input_enabled(True)

    async def handle_remaining_calls(self, remaining_calls, response_body, container, core, **kwargs):
        from frontend.pages.chatbot.coordinator import PipelineHandler
        pipeline = PipelineHandler(self)
        await pipeline.handle_remaining_calls(remaining_calls, response_body, container, core, **kwargs)

class FormErrorHandler:
    def display_error_boundary(self, container, title: str, message: str):
        from frontend.pages.chatbot.ui import UIOperations
        from frontend.utils.ui import _safe_ui_call
        UIOperations.safe_notify(f"{title}: {message}", type="negative")
        def _add_label():
            with container:
                ui.label(f"Error: {message}").classes('p-4 bg-red-50 text-red-700 rounded border border-red-200')
        _safe_ui_call(_add_label)

class ToolPicker(BaseHandler):
    def __init__(self, container, tool_registry, on_tool_selected):
        super().__init__()
        self.container = container
        self.tool_registry = tool_registry
        self.on_tool_selected = on_tool_selected

    async def show(self):
        from frontend.design_tokens import Design
        self.logger.info(f"ToolPicker.show started. Registry type: {type(self.tool_registry)}")
        
        menu = getattr(self.tool_registry, 'TOOL_MENU', {})
        if not menu:
            from frontend.chatbot.config import ToolRegistry
            menu = ToolRegistry.TOOL_MENU
            
        self.logger.info(f"ToolPicker.show menu source: {'Instance' if hasattr(self.tool_registry, 'TOOL_MENU') else 'Class'}. Items: {len(menu)}")
        
        with self.container:
            # Replicating original TOOL_PICKER_CLASSES
            picker_classes = (
                'w-full max-w-3xl min-w-0 mx-auto bg-gradient-to-br from-zinc-50 via-white to-zinc-100 '
                'border-2 border-[#505759]/40 shadow-lg rounded-xl text-base'
            )
            with ui.card().classes(picker_classes):
                with ui.row().classes(Design.PANEL_SHELL_HEADER):
                    ui.label("RescueBox Plugin Selector").classes(Design.PANEL_SHELL_HEADER_TITLE)
                
                with ui.column().classes("p-4 gap-3 w-full"):
                    ui.label("Choose a plugin to run:").classes("text-sm font-semibold text-zinc-700")
                    if not menu:
                        ui.label("No plugins available in TOOL_MENU.").classes("text-sm text-red-500")
                    else:
                        for num, tool in menu.items():
                            self.logger.info(f"Adding tool to UI: {num} - {tool.get('name')}")
                            row = ui.row().classes(
                                f"w-full min-w-0 py-2 px-3 rounded-lg {Design.CHATBOT_PLUGIN_MENU_ROW} cursor-pointer"
                            )
                            row.on('click', lambda *a, t=tool: self.on_tool_selected(t['endpoint'], {}))
                            with row:
                                ui.label(f'{num}. {tool["name"]} — {tool.get("desc", "No description")}').classes(
                                    'w-full text-left text-sm leading-snug font-medium text-zinc-900 '
                                    'whitespace-normal break-words'
                                )
        
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
            # Replicating original ANALYSIS_PICKER_CLASSES
            picker_classes = 'w-full max-w-2xl mx-auto bg-zinc-50 border-2 border-[#505759]/40 text-sm shadow-lg rounded-xl'
            with ui.card().classes(picker_classes):
                with ui.row().classes(Design.PANEL_SHELL_HEADER):
                    ui.label("Analysis Mode").classes(Design.PANEL_SHELL_HEADER_TITLE)
                
                with ui.column().classes("p-4 gap-3 w-full"):
                    ui.label("Select an analysis type:").classes("text-sm text-zinc-600")
                    options = ['Surface Scan', 'Deep Forensic', 'AI Content Analysis']
                    for a_type in options:
                        self.logger.info(f"Adding analysis option: {a_type}")
                        row = ui.row().classes(
                            f"w-full min-w-0 py-3 px-3 rounded-lg {Design.CHATBOT_PLUGIN_MENU_ROW} cursor-pointer"
                        )
                        row.on('click', lambda *a, t=a_type: self.on_analysis_selected(t))
                        with row:
                            ui.label(a_type).classes(
                                'w-full text-left text-sm leading-snug font-medium text-zinc-900'
                            )
        self.logger.info("AnalysisPicker.show finished building UI.")

def _compose_age_gender_pipeline_filter(gender, age_op, age_val):
    parts = []
    if gender: parts.append(f"Gender={gender}")
    if age_val is not None:
        sym = {"lt":"<", "lte":"<=", "eq":"=", "gt":">", "gte":">="}.get(age_op, "<")
        parts.append(f"Age {sym} {age_val}")
    return ", ".join(parts)

async def show_case_notes_dialog() -> Optional[str]:
    from frontend.design_tokens import Design
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    with ui.dialog() as dialog, ui.card().classes(Design.PANEL_SHELL_CARD_NARROW):
        with ui.row().classes(Design.PANEL_SHELL_HEADER):
            ui.label('Job Submission Details').classes(Design.PANEL_SHELL_HEADER_TITLE)
            ui.button(icon='close', on_click=lambda: (future.set_result(None), dialog.close())).props('flat round dense').classes(Design.PANEL_SHELL_HEADER_ICON)
        
        with ui.column().classes(Design.PANEL_SHELL_BODY + ' gap-4'):
            ui.label('Add optional notes for the case file:').classes('text-sm text-zinc-500')
            # Use rb-case-notes-field to ensure maroon/gray brand colors and no blue/indigo
            notes = ui.textarea(label='Case Notes').classes('w-full rb-case-notes-field').props('outlined')
        
        with ui.row().classes(Design.PANEL_SHELL_FOOTER + ' justify-end'):
            ui.button('Skip & Submit', on_click=lambda: (future.set_result(""), dialog.close())).classes(Design.BTN_MEDIUM_GRAY).props('outline')
            ui.button('Submit with Notes', on_click=lambda: (future.set_result(notes.value), dialog.close())).classes(Design.BTN_PRIMARY)
    dialog.open()
    return await future

from frontend.chatbot.multi_tool_handler import (
    apply_metadata_filter,
    batch_items_have_age_gender_metadata,
    chain_output_to_input,
    coerce_pipeline_response,
    extract_batch_file_items,
)
