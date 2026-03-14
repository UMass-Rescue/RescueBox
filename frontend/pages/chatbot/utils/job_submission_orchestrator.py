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
from frontend.chatbot.multi_tool_handler import chain_output_to_input
from frontend.components.shared.notifications import notify_info
from frontend.pages.chatbot.chatbot_forms import show_results, load_and_show_form
from frontend.chatbot import api_helpers
from nicegui import background_tasks
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
                        remaining_calls=None, conversation_id=None):
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

        Returns:
            None
        """
        try:
            await self._validate_and_prepare(request_body, endpoint, container)
            response_body, actual_conversation_id, job_info = await self._execute_job(request_body, endpoint, task_schema, container, core)
            # If the job was scheduled to run in background, _execute_job returns response_body=None.
            # In that case we should not call the immediate success handler (results will be shown when job completes).
            if response_body is not None:
                await self._handle_success(request_body, endpoint, task_schema, container, core, remaining_calls, actual_conversation_id, response_body, job_info)
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

    async def _execute_job(self, request_body, endpoint: str, task_schema, container, core):
        """Execute the actual job submission."""
        self.logger.info("Executing job submission for endpoint: %s", endpoint)

        # Ensure we have a conversation for saving messages
        conversation_id = await self.conversation_manager.ensure_conversation(
            endpoint, self.form_handler.state_manager
        )

        # Persist an assistant message indicating which tool will be used.
        # This is saved when the form is submitted so cancelling the form leaves no history.
        try:
            if conversation_id:
                await DatabaseService.save_message_to_history(
                    conversation_id,
                    role='assistant',
                    content=f"I'll use {endpoint} to help you.",
                    message_type='tool_selection'
                )
        except Exception:
            # Non-fatal: continue even if we cannot write to history
            self.logger.debug("Failed to save assistant 'I'll use' message to history (continuing).")

        # Also show the assistant message immediately in the live chat UI so the user
        # sees confirmation without waiting for the job to complete.
        try:
            from frontend.pages.chatbot.chatbot_message import ChatMessage, render_message
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
            try:
                from frontend.pages.chatbot.chatbot_forms import get_global_chat_container
                gc = get_global_chat_container()
                target_container = gc or container
            except Exception:
                target_container = container

            if target_container is not None:
                try:
                    logger.info("Rendering assistant selection message into container=%r (global_chat_container=%r provided_container=%r)",
                                target_container, getattr(gc, '__repr__', lambda: gc)(), container)
                    render_message(target_container, assistant_msg)
                    # Schedule scroll to bottom (use ui.timer from NiceGUI)
                    try:
                        ui = nicegui.ui
                        ui.timer(0.1, UIOperations.scroll_to_bottom, once=True)
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
        # Create job record (status=RUNNING) before submission so it can be recovered
        job_info = await DatabaseService.create_and_track_job(request_body, endpoint, task_schema, response_body=None)
        job_id = job_info.get('job_id') if job_info else None
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

        # Build API endpoint path using helper
        api_endpoint = api_helpers.make_api_path(core.config.RESCUEBOX_HOST, endpoint)

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
                        # show_results will handle container validity internally
                        logger.debug("job_submission_orchestrator: about to show_results container=%r job_id=%s", container, job_id)
                        await show_results(container=container, response_body=response_data, job_id=job_id)
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

                # Render a friendly assistant message into the chat so the user sees the validation error
                try:
                    from frontend.pages.chatbot.chatbot_message import ChatMessage, render_message
                    from frontend.pages.chatbot.chatbot_forms import get_global_chat_container
                    target_container = get_global_chat_container() or container
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

                # Ensure UI processing state cleared
                try:
                    if getattr(self.form_handler, 'state_manager', None):
                        try:
                            self.form_handler.state_manager.set_processing(False)
                            self.form_handler.state_manager.set_status("Ready")
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

        # Background job scheduled; clear processing state for the UI and inform user
        try:
            if getattr(self.form_handler, 'state_manager', None):
                try:
                    self.form_handler.state_manager.set_processing(False)
                    self.form_handler.state_manager.set_status("Background job scheduled")
                except Exception:
                    pass
        except Exception:
            pass

        # Return immediately; job will complete in background
        self.logger.info("Job %s scheduled for background submission for endpoint: %s", job_id, endpoint)
        return None, conversation_id, job_info

    async def _handle_success(self, _request_body, endpoint: str, task_schema, container, core,
                            remaining_calls, conversation_id, response_body, job_info=None):
        """Handle successful job completion."""

        # job_info is expected to be created before execution and completed already.
        job_id = job_info.get('job_id') if job_info else None
        # Save tool result using DatabaseService
        if conversation_id:
            await DatabaseService.save_tool_result_to_history(conversation_id, endpoint, job_id)

        # Show results
        await show_results(
            container=container,
            response_body=response_body,
            job_id=getattr(response_body, 'job_id', None)
        )

        # Scroll to bottom after results are rendered
        UIOperations.scroll_to_bottom()

        # Handle remaining calls in multi-call sequence
        if remaining_calls:
            await self.handle_remaining_calls(
                remaining_calls, response_body, container, core
            )

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

    async def handle_remaining_calls(self,
                                     remaining_calls: List[Dict[str, Any]],
                                     response_body,
                                     container,
                                     core,
                                     load_form_func: Optional[Callable] = None):
        """
        Handle remaining calls in a multi-call sequence.

        Args:
            remaining_calls: List of remaining tool calls
            response_body: Response from the current call
            container: UI container
            core: ChatbotCore instance
            load_form_func: Optional function to load next form
        """
        if not remaining_calls:
            return

        try:
            next_call = remaining_calls[0]
            next_endpoint = next_call['endpoint']
            next_arguments = next_call['arguments']

            # Get schema for next endpoint
            next_schema = await core.get_task_schema_from_endpoint(next_endpoint)
            if next_schema:
                # Chain output from current call to next call
                self.logger.info("Chaining output to next tool call: %s", next_endpoint)
                next_arguments = chain_output_to_input(response_body, next_arguments, next_schema)
                notify_info(f"Proceeding to next tool: {next_endpoint}")
            else:
                self.logger.warning("Could not get schema for next endpoint: %s", next_endpoint)

            # Load next form - import here to avoid circular imports
            await load_and_show_form(
                container=container,
                core=core,
                endpoint=next_endpoint,
                arguments=next_arguments,
                on_form_submit=self._create_next_form_handler(
                    remaining_calls[1:] if len(remaining_calls) > 1 else None,
                    container,
                    core
                )
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

    def _create_next_form_handler(self, remaining_calls, container, core):
        """Create a form handler for the next call in sequence."""
        async def handle_next_form(request_body, next_endpoint, task_schema):
            # Get current conversation_id from state manager
            conversation_id = self.form_handler.state_manager.conversation_id
            await self.submit_job(
                request_body, next_endpoint, task_schema,
                container, core, remaining_calls, conversation_id
            )
        return handle_next_form
