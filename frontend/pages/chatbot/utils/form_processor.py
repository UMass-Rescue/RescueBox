"""
Form Processor

Handles form submission and job processing.
"""

import logging
from typing import Optional, Dict, Any, Callable, List
from nicegui import ui

from frontend.pages.chatbot.utils.database_service import DatabaseService
from frontend.pages.chatbot.utils.ui_operations import UIOperations
from frontend.pages.chatbot.chatbot_forms import show_results
from frontend.pages.chatbot.utils.job_submission_orchestrator import JobSubmissionOrchestrator
from frontend.pages.chatbot.utils.form_error_handler import FormErrorHandler
from frontend.chatbot.config import ChatbotConfig
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.multi_tool_handler import chain_output_to_input
from frontend.components.shared.notifications import notify_info
from frontend.database import JobStatus
from frontend.database.job_db import get_job_db


class FormProcessor:
    """Handles form submission and job processing."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_handler = FormErrorHandler()

    async def process_form(self,
                          request_body,
                          endpoint: str,
                          task_schema,
                          core,
                          current_form_ref: dict,
                          chat_container,
                          show_results_func,
                          show_error_func,
                          conversation_id_ref: Optional[dict] = None,
                          remaining_calls: Optional[list] = None,
                          load_and_show_form_func: Optional[Callable] = None):
        """
        Process form submission through complete workflow.

        Args:
            request_body: RequestBody Pydantic model from form
            endpoint: API endpoint for job submission
            task_schema: TaskSchema for the endpoint
            core: ChatbotCore instance
            current_form_ref: Dict with current form widget
            chat_container: Container for chat messages
            show_results_func: Function to show results
            show_error_func: Function to show errors
            conversation_id_ref: Optional conversation ID reference
            remaining_calls: Remaining tool calls for multi-call sequence
            load_and_show_form_func: Function to load next form
        """
        self.logger.info("Processing form submission for endpoint: %s", endpoint)

        from frontend.utils.nicegui_storage import ensure_user_id
        if ensure_user_id() is None:
            return

        # Setup database and job
        job_db = await self._get_job_database()
        pipeline_total = (1 + len(remaining_calls)) if remaining_calls else None
        endpoint_chain_first = [endpoint] if endpoint else None
        job = await self._create_job_record(
            job_db,
            request_body,
            task_schema,
            endpoint,
            endpoint_chain=endpoint_chain_first,
            pipeline_total_steps=pipeline_total,
        )

        try:
            # Submit job
            response_body = await core.submit_job(request_body, endpoint)
            job_uid = getattr(response_body, 'job_id', None)

            if job and job_uid:
                await DatabaseService.complete_job(job_uid, response_body)

            try:
                from frontend.utils.nicegui_storage import get_user_id_for_jobs
                from frontend.database.pipeline_index_service import (
                    record_pipeline_job_completion,
                )

                _uid = get_user_id_for_jobs()
                if _uid and job_uid:
                    record_pipeline_job_completion(
                        _uid, job_uid, job_uid, endpoint, response_body
                    )
            except Exception as idx_e:
                self.logger.debug("Pipeline index (form processor) skipped: %s", idx_e)

            # Save results to chat history
            await self._save_success_to_history(conversation_id_ref, job_uid)

            await show_results(
                chat_container,
                response_body,
                job_uid,
                pipeline_total_steps=pipeline_total,
                remaining_calls_after_step=remaining_calls,
            )
            self.logger.info("Results displayed successfully")

            # Scroll to bottom only when no chained form follows (orchestrator scrolls the next form).
            if not (remaining_calls and load_and_show_form_func):
                UIOperations.scroll_to_bottom()

            # Handle remaining calls
            if remaining_calls and load_and_show_form_func:
                # Use JobSubmissionOrchestrator's logic for consistency
                # We pass None as the handler since we are providing the load_form_func callback
                orchestrator = JobSubmissionOrchestrator(None)
                root_uid = job.uid if job else None
                await orchestrator.handle_remaining_calls(
                    remaining_calls,
                    response_body,
                    chat_container,
                    core,
                    load_and_show_form_func,
                    accumulated_endpoint_chain=[endpoint],
                    pipeline_total_steps=pipeline_total,
                    pipeline_root_job_id=root_uid,
                    completed_step_job_id=job.uid if job else None,
                )

        except Exception as e:
            self.logger.error("Form processing failed for endpoint %s: %s", endpoint, str(e))

            # Handle job failure
            await self._handle_job_failure(job_db, job, str(e))

            # Save error to chat history
            await self._save_error_to_history(conversation_id_ref, str(e))

            # Show error boundary
            await show_error_func(str(e))

    async def _get_job_database(self):
        """Get job database instance."""
        return get_job_db()

    async def _create_job_record(
        self,
        job_db,
        request_body,
        task_schema,
        endpoint,
        *,
        endpoint_chain=None,
        pipeline_total_steps=None,
        pipeline_root_job_id=None,
    ):
        """Create job record in database (same pipeline columns as chat orchestrator)."""
        job = await job_db.create_job(
            request_body=request_body,
            task_schema=task_schema,
            endpoint=endpoint,
            endpoint_chain=endpoint_chain,
            pipeline_total_steps=pipeline_total_steps,
            pipeline_root_job_id=pipeline_root_job_id,
        )
        self.logger.info("Job %s created in database", job.uid)
        return job

    async def _save_success_to_history(self, conversation_id_ref: Optional[dict], job_uid: Optional[str]):
        """Save successful job completion to chat history."""
        if conversation_id_ref:
            conversation_id = conversation_id_ref.get('value')
            if conversation_id:
                try:
                    await DatabaseService.save_tool_result_to_history(conversation_id, '', job_uid)
                    self.logger.debug("Saved success to conversation %s", conversation_id)
                except Exception as e:
                    self.logger.warning("Failed to save success to chat history: %s", str(e))

    async def _handle_job_failure(self, job_db, job, error_message: str):
        """Handle job failure by updating status."""
        if job:
            try:
                await job_db.update_job_status(
                    job.uid,
                    JobStatus.FAILED,
                    status_text=error_message
                )
                self.logger.info("Job %s updated to Failed status", job.uid)
            except Exception as db_error:
                self.logger.warning("Failed to update job status to Failed: %s", str(db_error))

    async def _save_error_to_history(self, conversation_id_ref: Optional[dict], error_message: str):
        """Save error to chat history."""
        if conversation_id_ref:
            conversation_id = conversation_id_ref.get('value')
            if conversation_id:
                try:
                    await DatabaseService.save_error_to_history(conversation_id, '', error_message)
                    self.logger.debug("Saved error to conversation %s", conversation_id)
                except Exception as db_error:
                    self.logger.warning("Failed to save error to chat history: %s", str(db_error))
