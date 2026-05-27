from __future__ import annotations
import logging
import asyncio
from typing import Dict, Any, Callable, Optional, List
from nicegui import ui

from frontend.chatbot.config import ToolRegistry
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.message_handler import MessageHandler
from frontend.database.chat_history_db import get_chat_history_db
from frontend.pages.chatbot.state import ChatbotStateManager, ChatMessage
from frontend.pages.chatbot.database_service import DatabaseService
from frontend.pages.chatbot.handlers import (
    JobSubmissionOrchestrator,
    _compose_age_gender_pipeline_filter,
    apply_metadata_filter,
    batch_items_have_age_gender_metadata,
    chain_output_to_input,
    coerce_pipeline_response,
    extract_batch_file_items,
)
from frontend.pages.chatbot.ui import UIOperations, load_and_show_form, show_tool_picker, show_analysis_picker
from frontend.utils import notify_info, notify_warning

logger = logging.getLogger(__name__)

class FormSubmitHandler:
    """Handles form submission and job execution for the chatbot."""

    def __init__(self, state_manager: ChatbotStateManager):
        self.state_manager = state_manager
        # Lazy import to avoid circular dependency
        from frontend.pages.chatbot.handlers import JobSubmissionOrchestrator
        self.job_orchestrator = JobSubmissionOrchestrator(self)
        logger.debug("FormSubmitHandler initialized")

    async def submit_form(self,
                          request_body,
                          endpoint: str,
                          task_schema,
                          container,
                          core: ChatbotCore,
                          remaining_calls: Optional[List[Dict[str, Any]]] = None,
                          conversation_id: Optional[str] = None,
                          **kwargs):
        """Submit a form and handle the complete job execution flow."""
        from frontend.utils import ensure_user_id
        from frontend.pages.chatbot.handlers import show_case_notes_dialog
        from frontend.pages.chatbot.ui import UIOperations

        if ensure_user_id() is None:
            return False

        # Show case notes modal before submitting
        case_notes = await show_case_notes_dialog()
        if case_notes is None:
            logger.debug("User cancelled case notes dialog, aborting submission")
            return False

        if conversation_id:
            self.state_manager.set_conversation_id(conversation_id)
        await DatabaseService.ensure_active_conversation(self.state_manager)

        # Scroll to bottom to ensure the user sees the progress
        UIOperations.scroll_to_bottom()
        await self.job_orchestrator.submit_job(
            request_body, endpoint, task_schema, container, core,
            remaining_calls, self.state_manager.conversation_id,
            case_notes=case_notes or None, **kwargs
        )
        return True


class MessageFlowCoordinator:
    """Unified coordinator for all chatbot message processing workflows."""

    def __init__(self, state_manager: ChatbotStateManager, form_loader: Optional[Callable] = None):
        self.state_manager = state_manager
        self.form_loader = form_loader
        self.logger = logging.getLogger(__name__)

        # Initialize specialized handlers
        self.message_processor = MessageProcessor(state_manager, None)
        self.result_processor = ResultProcessor(state_manager, None)
        self.form_submit_handler = FormSubmitHandler(state_manager)

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
        core: Optional[Any] = None
    ) -> None:
        try:
            self.logger.info("Starting user message processing flow")
            result = await self.message_processor.send_message(
                message_text=message_text,
                add_message_callback=add_message_func,
                process_result_callback=self._create_result_processor(input_field, is_processing_ref, add_message_func, show_error_func, update_status_func, core),
                show_error_callback=show_error_func,
                update_status_callback=update_status_func
            )

            if result:
                await self._route_message_result(
                    result=result,
                    input_field=input_field,
                    is_processing_ref=is_processing_ref,
                    add_message_func=add_message_func,
                    show_error_func=show_error_func,
                    update_status_func=update_status_func
                )
        except Exception as e:
            self.logger.error("Error in message processing flow: %s", str(e))
            await show_error_func(f"Message processing failed: {str(e)}")

    def _create_result_processor(self, input_field, is_processing_ref, add_message_func, show_error_func, update_status_func, core):
        async def process_result(result: Dict[str, Any]) -> None:
            await self._route_message_result(
                result=result,
                input_field=input_field,
                is_processing_ref=is_processing_ref,
                add_message_func=add_message_func,
                show_error_func=show_error_func,
                update_status_func=update_status_func,
                core=core
            )
            is_processing_ref['value'] = False
            self.state_manager.set_processing(False)
        return process_result

    async def _route_message_result(self, result, input_field, is_processing_ref, add_message_func, show_error_func, update_status_func, core=None):
        callbacks = self._create_result_callbacks(input_field, is_processing_ref, add_message_func, show_error_func, update_status_func)
        coordinator_chat_container = getattr(self, 'chat_container', None)
        container_for_processing = coordinator_chat_container or input_field
        await self.result_processor.process_result(
            result=result,
            container=container_for_processing,
            core=core,
            **callbacks
        )

    def _create_result_callbacks(self, input_field, is_processing_ref, add_message_func, show_error_func, update_status_func) -> Dict[str, Callable]:
        def add_assistant_message_func(message, scroll_after=True):
            add_message_func(message, scroll_after)

        async def load_and_show_form_func(endpoint: str, arguments: dict, remaining_calls=None):
            if self.form_loader:
                await self.form_loader(endpoint, arguments, remaining_calls)

        return {
            'add_message_callback': add_assistant_message_func,
            'load_form_callback': load_and_show_form_func,
            'show_error_callback': show_error_func,
            'update_status_callback': update_status_func
        }

class MessageProcessor:
    """Handles message sending and processing for the chatbot."""

    def __init__(self, state_manager: ChatbotStateManager, message_handler: MessageHandler):
        self.state_manager = state_manager
        self.message_handler = message_handler

    async def send_message(self, message_text, add_message_callback, process_result_callback, show_error_callback, update_status_callback):
        try:
            self.state_manager.set_processing(True)
            self.state_manager.set_input_enabled(False)
            await asyncio.sleep(0)
            update_status_callback("Processing message...")
            logger.info("send_message: %s ", message_text)
            await DatabaseService.ensure_active_conversation(self.state_manager)
            user_message = ChatMessage('user', message_text)
            add_message_callback(user_message)
            await asyncio.sleep(0)

            if self.state_manager.conversation_id:
                chat_history = get_chat_history_db()
                logger.info("add_message: %s ", message_text)
                await chat_history.add_message(
                    conversation_id=self.state_manager.conversation_id,
                    role='user',
                    content=message_text
                )

            result = await self.message_handler.handle_message(message_text, update_status_callback)

            if result and result.get('type') == 'message':
                content = result.get('content', '')
                message = ChatMessage('assistant', content)
                add_message_callback(message)
                self.state_manager.set_processing(False)
                self.state_manager.clear_input()
                await asyncio.sleep(0.5)
                self.state_manager.set_input_enabled(True)
                update_status_callback("Rescuebox waiting for user..")
                return None
            elif result:
                self.state_manager.set_processing(False)
                await process_result_callback(result)
                self.state_manager.clear_input()
                result_type = result.get('type', '')
                if result_type in ('tool_picker', 'analysis_picker', 'show_form', 'multi_tool_calls'):
                    self.state_manager.set_input_enabled(False)
                else:
                    self.state_manager.set_input_enabled(True)
                
                if result_type == 'tool_picker':
                    update_status_callback("Select a tool from the menu above", scroll_after=False)
                elif result_type == 'analysis_picker':
                    update_status_callback("Choose an option from the menu above", scroll_after=False)
                elif result_type in ('show_form', 'multi_tool_calls'):
                    update_status_callback("Fill the Input form above and click Submit Job", scroll_to_form=True)
                else:
                    update_status_callback("Ready")
                return None

            self.state_manager.clear_input()
            self.state_manager.set_processing(False)
            self.state_manager.set_input_enabled(True)
            update_status_callback("Rescuebox waiting for user..")
            return result
        except Exception as e:
            logger.error("Error sending message: %s", str(e))
            self.state_manager.set_processing(False)
            show_error_callback(f"Failed to send message: {str(e)}")
            return None

class ResultProcessor:
    """Processes handler results and coordinates next actions."""

    def __init__(self, state_manager: ChatbotStateManager, tool_registry: ToolRegistry):
        self.state_manager = state_manager
        self.tool_registry = tool_registry

    async def process_result(self, result, container, core, add_message_callback, show_error_callback, update_status_callback, load_form_callback=None, set_input_enabled_callback=None):
        result_type = result.get('type', 'unknown')
        
        def _set_input(enabled: bool):
            if set_input_enabled_callback:
                try: set_input_enabled_callback(enabled)
                except Exception: pass

        try:
            if result_type == 'show_form':
                _set_input(False)
                endpoint = result.get('endpoint')
                arguments = result.get('arguments', {})
                if load_form_callback:
                    await load_form_callback(endpoint, arguments)
                else:
                    def _on_cancel():
                        if self.state_manager: self.state_manager.set_input_enabled(True)
                    await load_and_show_form(container, core, endpoint, arguments, self._create_form_submit_handler(container, core), on_form_cancel=_on_cancel)
                update_status_callback("Ready", scroll_after=False)
            elif result_type == 'multi_tool_calls':
                _set_input(False)
                tool_calls = result.get('tool_calls', [])
                notify_info(f"Processing {len(tool_calls)} tool call(s) sequentially...")
                if tool_calls and load_form_callback:
                    first_call = tool_calls[0]
                    await load_form_callback(first_call['endpoint'], first_call['arguments'], remaining_calls=tool_calls[1:] if len(tool_calls) > 1 else None)
            elif result_type == 'message':
                _set_input(True)
                message = ChatMessage('assistant', result.get('content', ''))
                add_message_callback(message)
            elif result_type == 'error':
                _set_input(True)
                show_error_callback(result.get('content', 'Unknown error'))
            elif result_type == 'help':
                _set_input(True)
                from frontend.components.chat import show_help_dialog
                show_help_dialog(result.get('content', 'No help available'), title="RescueBox Model Assistant Help")
            elif result_type == 'tool_picker':
                _set_input(False)
                container.clear()
                await show_tool_picker(container, self.tool_registry, self._create_tool_selected_handler(container, add_message_callback))
                update_status_callback("Ready", scroll_after=False)
            elif result_type == 'analysis_picker':
                _set_input(False)
                container.clear()
                await show_analysis_picker(container, self._create_analysis_selected_handler(container, add_message_callback))
                update_status_callback("Ready", scroll_after=False)
            else:
                _set_input(True)
                show_error_callback(f"Unknown response type: {result_type}")
            
            update_status_callback("Ready", scroll_to_form=False)
        except Exception as e:
            logger.error("Error processing result: %s", str(e))
            show_error_callback(f"Error processing response: {str(e)}")

    def _create_form_submit_handler(self, container, core):
        async def form_submit_handler(request_body, endpoint=None, task_schema=None, **kwargs):
            handler = FormSubmitHandler(self.state_manager)
            return await handler.submit_form(request_body, endpoint or kwargs.get('endpoint'), task_schema, container, core)
        return form_submit_handler

    def _create_tool_selected_handler(self, container, add_message_callback):
        async def tool_selected_handler(endpoint, arguments):
            from frontend.pages.chatbot.ui import show_tool_selection
            await show_tool_selection(container, endpoint)
        return tool_selected_handler

    def _create_analysis_selected_handler(self, container, add_message_callback):
        async def analysis_selected_handler(analysis_type):
            message = ChatMessage('assistant', f"Selected analysis: {analysis_type}")
            add_message_callback(message)
        return analysis_selected_handler

class PipelineHandler:
    """Handles multi-step job submission workflows."""

    def __init__(self, orchestrator: JobSubmissionOrchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)

    async def handle_remaining_calls(self, remaining_calls, response_body, container, core, load_form_func=None, accumulated_endpoint_chain=None, pipeline_total_steps=None, pipeline_root_job_id=None, completed_step_job_id=None):
        if not remaining_calls: return
        try:
            response_body = coerce_pipeline_response(response_body)
            next_call = remaining_calls[0]
            next_endpoint = next_call['endpoint']
            next_arguments = next_call['arguments']

            next_schema = await core.get_task_schema_from_endpoint(next_endpoint)
            if next_schema:
                next_arguments = chain_output_to_input(response_body, next_arguments, next_schema)

            filtered_paths = None
            items = extract_batch_file_items(response_body)
            if items:
                if batch_items_have_age_gender_metadata(items):
                    criteria = await self._show_filter_criteria_dialog(container)
                else:
                    criteria = ""
                filtered_paths = apply_metadata_filter(items, criteria)
                if completed_step_job_id and batch_items_have_age_gender_metadata(items):
                    try:
                        from frontend.database import get_job_db
                        jdb = get_job_db()
                        await jdb.update_job_pipeline_metadata_filter_criteria(completed_step_job_id, criteria)
                    except Exception: pass
            
            def _on_cancel():
                if self.orchestrator.form_handler.state_manager:
                    self.orchestrator.form_handler.state_manager.set_input_enabled(True)

            with container:
                if items and criteria and criteria.strip() and not filtered_paths:
                    notify_warning("No files matched your filter; the next step will process no images.")
                if next_schema:
                    notify_info(f"Proceeding to next operation: {next_endpoint}")
                
                await load_and_show_form(container, core, next_endpoint, next_arguments, self._create_next_form_handler(remaining_calls[1:] if len(remaining_calls) > 1 else None, container, core, filtered_paths, accumulated_endpoint_chain, pipeline_total_steps, pipeline_root_job_id), on_form_cancel=_on_cancel)
                try: await UIOperations.safe_container_update(container)
                except Exception: pass
                UIOperations.scroll_form_into_view_with_retries(client=getattr(container, 'client', None))
        except Exception as e:
            self.logger.error("Error handling remaining calls: %s", str(e))

    async def _show_filter_criteria_dialog(self, container) -> str:
        from frontend.pages.chatbot.handlers import _compose_age_gender_pipeline_filter
        loop = asyncio.get_running_loop()
        future: asyncio.Future[str] = loop.create_future()
        def _finish(value: str):
            if not future.done(): future.set_result(value.strip())
        with container:
            with ui.dialog() as dialog, ui.card().classes('w-[400px]'):
                ui.label('Filter files before next step').classes('text-lg font-semibold')
                gender_select = ui.select(options={'': 'Any gender', 'male': 'Male', 'female': 'Female'}, value='', label='Gender').classes('w-full mt-2')
                with ui.row().classes('w-full items-end gap-2 flex-wrap'):
                    age_op_select = ui.select(options={'lt':'Less than','lte':'At most','eq':'Equals','gt':'Greater than','gte':'At least'}, value='lt', label='Compare').classes('min-w-[9rem] flex-1')
                    age_number = ui.number(label='Years', value=None, min=0, max=120, format='%.0f').classes('min-w-[6rem] flex-1')
                def _use_all(): _finish(''); dialog.close()
                def _apply_filter():
                    raw = age_number.value
                    age_val = None
                    if raw is not None and raw != '':
                        try: age_val = float(raw)
                        except: notify_warning('Enter a valid age number, or leave age empty.'); return
                    crit = _compose_age_gender_pipeline_filter(str(gender_select.value or ''), str(age_op_select.value or 'lt'), age_val)
                    _finish(crit.strip()); dialog.close()
                with ui.row().classes('mt-4 gap-2'):
                    ui.button('Use all', on_click=_use_all)
                    ui.button('Apply filter', on_click=_apply_filter)
            dialog.open()
        try: return await asyncio.wait_for(future, timeout=120.0)
        except: return ''

    def _create_next_form_handler(self, remaining_calls, container, core, filtered_paths=None, accumulated_endpoint_chain=None, pipeline_total_steps=None, pipeline_root_job_id=None):
        async def handle_next_form(request_body, endpoint=None, task_schema=None, **kwargs):
            # Support both parameter names 'next_endpoint' (legacy) and 'endpoint' (current)
            effective_endpoint = endpoint or kwargs.get('next_endpoint') or kwargs.get('endpoint')
            
            if filtered_paths is not None:
                ff_value = {"files": [{"path": p} for p in filtered_paths]}
                if isinstance(request_body, dict):
                    request_body.setdefault("inputs", {})["file_filter"] = ff_value
                else:
                    inputs = getattr(request_body, "inputs", None)
                    if isinstance(inputs, dict): inputs["file_filter"] = ff_value
                    elif inputs is not None:
                        try: setattr(inputs, "file_filter", ff_value)
                        except: pass
            conversation_id = self.orchestrator.form_handler.state_manager.conversation_id
            chain = list(accumulated_endpoint_chain or []) + [effective_endpoint]
            await self.orchestrator.submit_job(request_body, effective_endpoint, task_schema, container, core, remaining_calls, conversation_id, endpoint_chain=chain, pipeline_total_steps=pipeline_total_steps, pipeline_root_job_id=pipeline_root_job_id)
        return handle_next_form
