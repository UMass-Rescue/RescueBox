"""
Job Submission Orchestrator.

Handles the complete job submission workflow orchestration.
"""

import logging
from typing import Dict, Any, List, Optional, Callable

 
from frontend.pages.chatbot.utils.ui_operations import UIOperations
from frontend.pages.chatbot.utils.database_service import DatabaseService
from frontend.pages.chatbot.utils.form_error_handler import FormErrorHandler
from frontend.pages.chatbot.utils.form_validator import FormValidator
from frontend.pages.chatbot.utils.conversation_manager import ConversationManager
from frontend.chatbot.multi_tool_handler import (
    chain_output_to_input,
    coerce_pipeline_response,
    extract_batch_file_items,
    apply_metadata_filter,
    batch_items_have_age_gender_metadata,
)
from frontend.components.shared.notifications import notify_info, notify_warning
from frontend.pages.chatbot.chatbot_forms import show_results, load_and_show_form
from frontend.chatbot import api_helpers
from nicegui import background_tasks, ui
import asyncio


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class JobSubmissionOrchestrator:
    """Orchestrates the complete job submission workflow."""

    def __init__(self, form_handler):
        """
        Initialize job submission orchestrator.

        Args:
            form_handler: FormSubmitHandler instance
        """
        self.form_handler = form_handler
        self.logger = logging.getLogger(__name__)
        self.error_handler = FormErrorHandler()
        self.form_validator = FormValidator()
        self.conversation_manager = ConversationManager()

    async def submit_job(self, request_body, endpoint: str, task_schema, container, core,
                        remaining_calls=None, conversation_id=None, case_notes: str = None,
                        endpoint_chain: Optional[List[str]] = None,
                        pipeline_total_steps: Optional[int] = None):
        """
        Submit a job and handle the complete workflow.

        Args:
            request_body: Validated request body
            endpoint: API endpoint name
            task_schema: Task schema for the endpoint
            container: UI container for displaying results
            core: ChatbotCore instance
            remaining_calls: Remaining tool calls in sequence
            conversation_id: Conversation ID for message saving
            pipeline_total_steps: Total steps in multi-tool pipeline; inferred from remaining_calls when omitted

        Returns:
            None
        """
        try:
            from frontend.utils.nicegui_storage import ensure_user_id
            if ensure_user_id() is None:
                return

            # Infer total only when there are more steps after this one (do not treat [] as "1 step").
            if pipeline_total_steps is None and remaining_calls and len(remaining_calls) > 0:
                pipeline_total_steps = 1 + len(remaining_calls)

            await self._validate_and_prepare(request_body, endpoint, container)
            response_body, actual_conversation_id, job_info = await self._execute_job(
                request_body, endpoint, task_schema, container, core, remaining_calls, case_notes,
                endpoint_chain=endpoint_chain, pipeline_total_steps=pipeline_total_steps,
            )
            # If the job was scheduled to run in background, _execute_job returns response_body=None.
            # In that case we should not call the immediate success handler (results will be shown when job completes).
            if response_body is not None:
                await self._handle_success(
                    request_body, endpoint, task_schema, container, core, remaining_calls,
                    actual_conversation_id, response_body, job_info,
                    pipeline_total_steps=pipeline_total_steps,
                )
            else:
                # Background job scheduled; leave UI state to background worker and return
                self.logger.info("Background job scheduled; returning to caller (job_info: %s)", job_info)
                return
        except Exception as e:
            await self._handle_submission_error(e, endpoint, container, conversation_id)

    async def _validate_and_prepare(self, request_body, endpoint: str, container):
        """Validate request and prepare for submission."""
        await self.form_validator.validate_and_prepare(
            request_body, endpoint, self.form_handler.state_manager, container
        )

    async def _execute_job(self, request_body, endpoint: str, task_schema, container, core, remaining_calls=None, case_notes: str = None,
                           endpoint_chain: Optional[List[str]] = None,
                           pipeline_total_steps: Optional[int] = None):
        """Execute the actual job submission."""
        self.logger.info("Executing job submission for endpoint: %s", endpoint)

        # Ensure we have a conversation for saving messages
        conversation_id = await self.conversation_manager.ensure_conversation(
            endpoint, self.form_handler.state_manager
        )

        # Persist a user row when the conversation has no chat prompt yet (form-only / tool-first flows).
        # Without this, history load shows assistant/tool lines but no YOU: bubble.
        saved_user_text = await DatabaseService.save_user_prompt_if_missing_from_form_submission(
            conversation_id, request_body, endpoint
        )
        if saved_user_text:
            try:
                from frontend.pages.chatbot.chatbot_message import ChatMessage, render_message
                from frontend.pages.chatbot.chatbot_forms import get_global_chat_container
                um = ChatMessage('user', saved_user_text)
                if getattr(self.form_handler, 'state_manager', None):
                    self.form_handler.state_manager.add_message(um)
                target = None
                try:
                    target = get_global_chat_container()
                except Exception:
                    target = None
                target = target or container
                if target is not None:
                    render_message(target, um)
            except Exception:
                self.logger.debug("Could not render synthetic user prompt in chat UI (continuing).")

        # Persist an assistant message indicating which tool will be used.
        # This is saved when the form is submitted so cancelling the form leaves no history.
        try:
            if conversation_id:
                await DatabaseService.save_message_to_history(
                    conversation_id,
                    role='assistant',
                    content=f"I'll use {endpoint} to help you.",
                    message_type='tool_selection',
                    tool_call_endpoint=endpoint,
                )
        except Exception:
            # Non-fatal: continue even if we cannot write to history
            self.logger.debug("Failed to save assistant 'I'll use' message to history (continuing).")

        # Also show the assistant message immediately in the live chat UI so the user
        # sees confirmation without waiting for the job to complete.
        try:
            from frontend.pages.chatbot.chatbot_message import ChatMessage
            from frontend.components.results.tool_selection_card import render_tool_selection_message
            import nicegui
            # Create message and add to in-memory state manager for UI rendering
            assistant_msg = ChatMessage('assistant', f"I'll use {endpoint} to help you.", message_type='tool_selection')
            # Add to state_manager if available
            if getattr(self.form_handler, 'state_manager', None):
                try:
                    self.form_handler.state_manager.add_message(assistant_msg)
                except Exception:
                    pass
            # Render into the main chat container (prefer global chat container) so the assistant
            # selection message appears in the conversation rather than inside any input-area wrapper.
            gc = None
            try:
                from frontend.pages.chatbot.chatbot_forms import get_global_chat_container
                gc = get_global_chat_container()
                target_container = gc or container
            except Exception:
                target_container = container

            if target_container is not None:
                try:
                    logger.info("Rendering assistant selection message into container=%r (global_chat_container=%r provided_container=%r)",
                                target_container, gc, container)
                    render_tool_selection_message(target_container, endpoint)
                    # Schedule scroll to bottom (use ui.timer from NiceGUI)
                    try:
                        ui = nicegui.ui
                        _jc = getattr(target_container, 'client', None)
                        ui.timer(0.1, lambda c=_jc: UIOperations.scroll_to_bottom(client=c), once=True)
                    except Exception:
                        pass
                except Exception:
                    # ignore rendering errors
                    pass
        except Exception:
            # UI update is best-effort; don't fail job submission if it fails
            self.logger.debug("Failed to render assistant message in UI (continuing).")

        # Save tool call to conversation history
        await self.conversation_manager.save_tool_call(conversation_id, request_body, endpoint)
        # Capture user_id while we have request context (before any background tasks)
        try:
            from frontend.utils.nicegui_storage import get_user_id_for_jobs
            user_id = get_user_id_for_jobs()
        except Exception:
            user_id = None
        # Create job record (status=RUNNING) before submission so it can be recovered
        job_info = await DatabaseService.create_and_track_job(
            request_body, endpoint, task_schema, response_body=None, case_notes=case_notes, user_id=user_id,
            endpoint_chain=endpoint_chain,
        )
        job_id = job_info.get('job_id') if job_info else None
        try:
            from frontend.pages.chatbot.utils.chat_ui_builder import refresh_chat_history_button_visibility

            refresh_chat_history_button_visibility()
        except Exception:
            pass
        # Save a job-started marker in chat history for recovery
        try:
            await DatabaseService.save_job_started_to_history(conversation_id, endpoint, job_id)
        except Exception:
            pass

        # Build request dict for submission (serializable)
        request_dict = {
            'inputs': {k: v.model_dump(mode='json') if hasattr(v, 'model_dump') else v for k, v in request_body.inputs.items()},
            'parameters': request_body.parameters
        }
        if 'file_filter' in request_body.inputs:
            ff = request_dict.get('inputs', {}).get('file_filter', {})
            n = len(ff.get('files', [])) if isinstance(ff, dict) else 0
            self.logger.info("Request includes file_filter: %d paths (keys: %s)", n, list(request_dict.get('inputs', {}).keys()))

        # Build API endpoint path using helper
        api_endpoint = api_helpers.make_api_path(core.config.RESCUEBOX_HOST, endpoint)

        # Create "Job running" message with updatable label (before _do_submit so closure captures it)
        running_label_ref = []
        try:
            from frontend.pages.chatbot.chatbot_message import ChatMessage
            from frontend.pages.chatbot.chatbot_forms import get_global_chat_container
            target = container or get_global_chat_container()
            if target is not None:
                with target:
                    with ui.row().classes('w-full items-start'):
                        with ui.card().classes('bg-gray-200 max-w-sm shadow-sm'):
                            with ui.column().classes('p-1.5 w-full gap-1'):
                                ui.label('🤖 Assistant').classes('font-medium text-xs')
                                content_label = ui.label("🔄 Job running...").classes('text-sm')
                                running_label_ref.append(content_label)
                try:
                    self.form_handler.state_manager.add_message(ChatMessage('assistant', "🔄 Job running..."))
                except Exception:
                    pass
                _run_client = getattr(target, 'client', None)
                ui.timer(0.1, lambda c=_run_client: UIOperations.scroll_to_bottom(client=c), once=True)
        except Exception as render_err:
            self.logger.debug("Could not render job running message: %s", render_err)

        async def _do_submit():
            try:
                # Use api_helpers.post_job to submit and get resolved dict
                response_data = await api_helpers.post_job(core.api if hasattr(core, 'api') else None, core.api_client, core.config, api_endpoint, request_dict)

                # Persist completion in job DB
                if job_id:
                    try:
                        await DatabaseService.complete_job(job_id, response_data)
                    except Exception as db_e:
                        self.logger.warning("Failed to mark job %s completed: %s", job_id, db_e)

                # Save result to conversation history
                if conversation_id:
                    try:
                        await DatabaseService.save_tool_result_to_history(conversation_id, endpoint, job_id)
                    except Exception:
                        pass

                # Safe UI update: only attempt if container/client still exists
                try:
                    if container is not None:
                        _ = container.client
                        # Update "Job running" to "Job completed" before showing results
                        if running_label_ref:
                            try:
                                running_label_ref[0].text = "✅ Job completed"
                            except Exception:
                                pass
                        # show_results will handle container validity internally
                        logger.info("job_submission_orchestrator: about to show_results container=%r job_id=%s", container, job_id)
                        await show_results(
                            container=container,
                            response_body=response_data,
                            job_id=job_id,
                            pipeline_total_steps=pipeline_total_steps,
                            remaining_calls_after_step=remaining_calls,
                        )
                        try:
                            await UIOperations.scroll_to_bottom_after_dom_update(container)
                        except Exception:
                            pass
                        # Handle remaining calls in multi-call sequence (filter dialog + next form)
                        if remaining_calls:
                            resp = coerce_pipeline_response(response_data) if isinstance(response_data, dict) else response_data
                            accumulated: Optional[List[str]] = None
                            if job_id:
                                try:
                                    from frontend.database import get_job_db
                                    jdb = get_job_db()
                                    rec = await jdb.get_job_by_uid(job_id)
                                    if rec and getattr(rec, 'endpointChain', None):
                                        accumulated = list(rec.endpointChain)
                                except Exception:
                                    accumulated = None
                            if not accumulated:
                                accumulated = [endpoint]
                            await self.handle_remaining_calls(
                                remaining_calls, resp, container, core,
                                accumulated_endpoint_chain=accumulated,
                                pipeline_total_steps=pipeline_total_steps,
                            )
                            # Next form is showing - stay disabled (rule: input only when no pending interaction)
                        else:
                            # No more forms - ready for new prompt
                            try:
                                if getattr(self.form_handler, 'state_manager', None):
                                    self.form_handler.state_manager.set_input_enabled(True)
                            except Exception:
                                pass
                        # Pipeline may add more UI after show_results; one more pass after that lands.
                        try:
                            _sc = container.client
                            UIOperations.scroll_to_bottom(client=_sc)
                        except Exception:
                            pass
                        # Ensure processing state cleared after background UI update
                        try:
                            if getattr(self.form_handler, 'state_manager', None):
                                self.form_handler.state_manager.set_processing(False)
                                self.form_handler.state_manager.set_status("Ready")
                        except Exception:
                            pass
                except Exception:
                    # Client deleted or UI not available; skip UI update
                    self.logger.info("UI not available to update job %s results", job_id)

            except Exception as e:
                self.logger.error("Background job submission failed for %s: %s", endpoint, str(e))
                # Try to extract structured error details for HTTPStatusErrors (e.g., 422)
                err_text = str(e)
                try:
                    import httpx as _httpx
                    if isinstance(e, _httpx.HTTPStatusError) and getattr(e, 'response', None):
                        try:
                            details = await api_helpers.resolve_json_response(core.api if hasattr(core, 'api') else None, e.response)
                            err_text = f"HTTP {e.response.status_code} - {details}"
                        except Exception:
                            # fallback to response text
                            try:
                                err_text = f"HTTP {e.response.status_code} - {getattr(e.response, 'text', str(e))}"
                            except Exception:
                                err_text = str(e)
                except Exception:
                    # non-httpx errors or resolution failed, keep string representation
                    err_text = str(e)

                # Update "Job running" to "Job failed" and render error details
                if running_label_ref:
                    try:
                        running_label_ref[0].text = "❌ Job failed"
                    except Exception:
                        pass
                try:
                    from frontend.pages.chatbot.chatbot_message import ChatMessage, render_message
                    from frontend.pages.chatbot.chatbot_forms import get_global_chat_container
                    target_container = container or get_global_chat_container()
                    friendly = ChatMessage('assistant', f"⚠️ Job submission failed: {err_text}")
                    try:
                        render_message(target_container, friendly)
                    except Exception:
                        # best-effort UI render; ignore if it fails
                        pass
                except Exception:
                    pass

                if job_id:
                    try:
                        await DatabaseService.update_job_status(job_id, 'FAILED', status_text=err_text)
                        if conversation_id:
                            await DatabaseService.save_error_to_history(conversation_id, endpoint, err_text, raw_error=str(e))
                    except Exception:
                        pass

                # Ensure processing state cleared; enable input (no retry button - user starts new run)
                try:
                    if getattr(self.form_handler, 'state_manager', None):
                        try:
                            self.form_handler.state_manager.set_processing(False)
                            self.form_handler.state_manager.set_status("Ready")
                            self.form_handler.state_manager.set_input_enabled(True)
                        except Exception:
                            pass
                except Exception:
                    pass

        # Schedule background submission so it survives UI navigation
        try:
            background_tasks.create(_do_submit(), name=f"job-{job_id}", handle_exceptions=True)
        except Exception:
            # Fallback to asyncio task if background_tasks not available
            asyncio.create_task(_do_submit())

        # Keep processing state and show "Job running" so user sees status (like smart analyze)
        try:
            if getattr(self.form_handler, 'state_manager', None):
                try:
                    self.form_handler.state_manager.set_processing(True)
                    self.form_handler.state_manager.set_status("🔄 Job running...")
                except Exception:
                    pass
        except Exception:
            pass

        # Return immediately; job will complete in background
        self.logger.info("Job %s scheduled for background submission for endpoint: %s", job_id, endpoint)
        return None, conversation_id, job_info

    async def _handle_success(self, _request_body, endpoint: str, task_schema, container, core,
                            remaining_calls, conversation_id, response_body, job_info=None,
                            pipeline_total_steps: Optional[int] = None):
        """Handle successful job completion."""

        # job_info is expected to be created before execution and completed already.
        job_id = job_info.get('job_id') if job_info else None
        # Save tool result using DatabaseService
        if conversation_id:
            await DatabaseService.save_tool_result_to_history(conversation_id, endpoint, job_id)

        rid = getattr(response_body, 'job_id', None) or job_id

        # Show results
        await show_results(
            container=container,
            response_body=response_body,
            job_id=rid,
            pipeline_total_steps=pipeline_total_steps,
            remaining_calls_after_step=remaining_calls,
        )

        await UIOperations.scroll_to_bottom_after_dom_update(container)

        # Handle remaining calls in multi-call sequence
        if remaining_calls:
            accumulated: Optional[List[str]] = None
            if job_id:
                try:
                    from frontend.database import get_job_db
                    jdb = get_job_db()
                    rec = await jdb.get_job_by_uid(job_id)
                    if rec and getattr(rec, 'endpointChain', None):
                        accumulated = list(rec.endpointChain)
                except Exception:
                    accumulated = None
            if not accumulated:
                accumulated = [endpoint]
            await self.handle_remaining_calls(
                remaining_calls, response_body, container, core,
                accumulated_endpoint_chain=accumulated,
                pipeline_total_steps=pipeline_total_steps,
            )
            # Next form showing - stay disabled
            try:
                _hc = container.client
                UIOperations.scroll_to_bottom(client=_hc)
            except Exception:
                pass
        else:
            self.form_handler.state_manager.set_input_enabled(True)

        # Clear processing state
        self.form_handler.state_manager.set_processing(False)
        self.form_handler.state_manager.set_status("Ready")

    async def _handle_submission_error(self, error: Exception, endpoint: str, container, conversation_id):
        """Handle various types of submission errors at orchestration level."""
        # Ignore "client deleted" errors which happen on page refresh/navigation
        if isinstance(error, RuntimeError) and 'deleted' in str(error):
            self.logger.info("Job submission UI update skipped: client was deleted")
            return

        error_msg = self.error_handler.clean_error_message(str(error))
        self.logger.error("Job submission orchestration failed for endpoint %s: %s", endpoint, error_msg)

        # For now, just re-raise the error - the caller should handle it
        # This maintains the existing behavior where errors bubble up
        raise error

    async def _show_filter_criteria_dialog(self, container) -> str:
        """Show dialog to collect filter criteria; returns criteria string or empty for all."""
        loop = asyncio.get_running_loop()
        future: asyncio.Future[str] = loop.create_future()

        def _finish(value: str) -> None:
            if not future.done():
                future.set_result(value.strip())

        with container:
            with ui.dialog() as dialog, ui.card().classes('w-[400px]'):
                ui.label('Filter files before next step').classes('text-lg font-semibold')
                ui.label(
                    'e.g. Gender=Male, Age<10, or Age < 10 (spaces optional). Leave empty to use all.'
                ).classes('text-sm text-gray-600')
                inp = ui.input(placeholder='Gender:Female, Age < 10').classes('w-full mt-2')
                with ui.row().classes('mt-4 gap-2'):
                    # Resolve value before closing so NiceGUI does not drop input state on close
                    ui.button('Use all', on_click=lambda: (_finish(''), dialog.close()))
                    ui.button(
                        'Apply filter',
                        on_click=lambda: (_finish(inp.value or ''), dialog.close()),
                    )
            dialog.open()
        try:
            return await asyncio.wait_for(future, timeout=120.0)
        except asyncio.TimeoutError:
            return ''

    async def handle_remaining_calls(self,
                                     remaining_calls: List[Dict[str, Any]],
                                     response_body,
                                     container,
                                     core,
                                     load_form_func: Optional[Callable] = None,
                                     accumulated_endpoint_chain: Optional[List[str]] = None,
                                     pipeline_total_steps: Optional[int] = None):
        """
        Handle remaining calls in a multi-call sequence.

        Args:
            remaining_calls: List of remaining tool calls
            response_body: Response from the current call
            container: UI container
            core: ChatbotCore instance
            load_form_func: Optional function to load next form
            pipeline_total_steps: Total steps in the pipeline (for nested submit_job)
        """
        if not remaining_calls:
            return

        try:
            response_body = coerce_pipeline_response(response_body)
            self.logger.info(
                "handle_remaining_calls: next=%s response_class=%s root_class=%s",
                remaining_calls[0].get("endpoint") if remaining_calls else None,
                type(response_body).__name__,
                type(getattr(response_body, "root", None)).__name__
                if getattr(response_body, "root", None) is not None
                else "None",
            )

            next_call = remaining_calls[0]
            next_endpoint = next_call['endpoint']
            next_arguments = next_call['arguments']

            # Get schema for next endpoint
            next_schema = await core.get_task_schema_from_endpoint(next_endpoint)
            if next_schema:
                self.logger.info("Chaining output to next tool call: %s", next_endpoint)
                next_arguments = chain_output_to_input(response_body, next_arguments, next_schema)
            else:
                self.logger.warning("Could not get schema for next endpoint: %s", next_endpoint)

            # If previous step produced batch files with metadata, ask for filter criteria
            filtered_paths: Optional[List[str]] = None
            items = extract_batch_file_items(response_body)
            if items:
                # this needs to be more generic 
                # Age/Gender filter UI only applies when the *previous* step produced classifier
                # metadata (Gender, Age). Image search / CLIP rows only have Query, Similarity, etc.
                if batch_items_have_age_gender_metadata(items):
                    criteria = await self._show_filter_criteria_dialog(container)
                else:
                    criteria = ""
                    self.logger.info(
                        "Pipeline metadata filter not shown: no Age/Gender metadata on prior step "
                        "(next_endpoint=%s, batch_item_count=%d) — passing all files.",
                        next_endpoint,
                        len(items),
                    )
                self.logger.info(
                    "Pipeline metadata filter (user input): next_endpoint=%s criteria=%r "
                    "(empty means pass all files) batch_item_count=%d",
                    next_endpoint,
                    criteria,
                    len(items),
                )
                filtered_paths = apply_metadata_filter(items, criteria)
                # Empty criteria => apply_metadata_filter already returns all paths.
                # Non-empty criteria with no matches => keep [] (do not fall back to all files).
                if criteria and criteria.strip() and not filtered_paths:
                    notify_warning(
                        "No files matched your filter; the next step will process no images.",
                    )
                self.logger.info(
                    "Pipeline metadata filter (result): matched_count=%d matched_paths=%s",
                    len(filtered_paths),
                    filtered_paths,
                )
            else:
                self.logger.warning(
                    "Pipeline metadata filter skipped: no batch file items extracted for chaining step "
                    "(next_endpoint=%s). Chaining still proceeds; file_filter will not be applied.",
                    next_endpoint,
                )
                notify_warning(
                    "Previous step did not return per-file metadata; the next job will use all images "
                    "(pipeline filter unavailable).",
                )

            # All UI creation must run inside container (background task has no slot stack)
            def _on_cancel():
                try:
                    if getattr(self.form_handler, 'state_manager', None):
                        self.form_handler.state_manager.set_input_enabled(True)
                except Exception:
                    pass

            with container:
                if next_schema:
                    notify_info(f"Proceeding to next tool: {next_endpoint}")
                await load_and_show_form(
                    container=container,
                    core=core,
                    endpoint=next_endpoint,
                    arguments=next_arguments,
                    on_form_submit=self._create_next_form_handler(
                        remaining_calls[1:] if len(remaining_calls) > 1 else None,
                        container,
                        core,
                        filtered_paths=filtered_paths,
                        accumulated_endpoint_chain=accumulated_endpoint_chain,
                        pipeline_total_steps=pipeline_total_steps,
                    ),
                    on_form_cancel=_on_cancel
                )

        except Exception as e:
            self.logger.error("Error handling remaining calls: %s", str(e))

    def _display_error_boundary(self, container, title: str, message: str, technical_details: str = None, icon: str = "error"):
        """
        Display a user-friendly error boundary with recovery options.

        Args:
            container: UI container to display error in
            title: Error title (e.g., "Network Error")
            message: User-friendly error message
            technical_details: Technical details for debugging
            icon: Material icon name for the error
        """
        self.error_handler.display_error_boundary(container, title, message, technical_details, icon)

    def _clean_error_message(self, raw_error: str) -> str:
        """Clean up error message to make it more user-friendly."""
        return self.error_handler.clean_error_message(raw_error)

    def _create_next_form_handler(self, remaining_calls, container, core, filtered_paths: Optional[List[str]] = None,
                                  accumulated_endpoint_chain: Optional[List[str]] = None,
                                  pipeline_total_steps: Optional[int] = None):
        """Create a form handler for the next call in sequence."""
        async def handle_next_form(request_body, next_endpoint, task_schema):
            # Inject file_filter (hidden) when previous step was BatchFileResponse + filter dialog.
            # Use ``is not None`` so an empty list still sends files: [] (process no images), not "all files".
            if filtered_paths is not None:
                if isinstance(request_body.inputs, dict):
                    request_body.inputs["file_filter"] = {"files": [{"path": p} for p in filtered_paths]}
                    self.logger.info(
                        "Pipeline file_filter injection for next job: endpoint=%s file_count=%d paths=%s",
                        next_endpoint,
                        len(filtered_paths),
                        filtered_paths,
                    )
            conversation_id = self.form_handler.state_manager.conversation_id
            chain = list(accumulated_endpoint_chain or []) + [next_endpoint]
            await self.submit_job(
                request_body, next_endpoint, task_schema,
                container, core, remaining_calls, conversation_id,
                endpoint_chain=chain,
                pipeline_total_steps=pipeline_total_steps,
            )
        return handle_next_form
