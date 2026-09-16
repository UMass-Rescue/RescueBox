from __future__ import annotations

import logging
from typing import Any

from nicegui import background_tasks, ui

from frontend.chatbot.config import ToolRegistry
from frontend.components.chat import UIOperations
from frontend.components.shared import render_loading_row
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.job_progress import (
    JobProgressPoller,
    cleanup_job_progress,
    init_job_progress,
)
from frontend.pages.chatbot.ui_flow import show_results
from frontend.utils.ui import _safe_ui_call

from .base import BaseHandler, FormErrorHandler
from .job_lifecycle_service import JobLifecycleService
from .job_submit_params import JobSubmitParams
from .pipeline import PipelineHandler

logger = logging.getLogger(__name__)


def _delete_loading_row(loading_row) -> None:
    if loading_row and hasattr(loading_row, "delete"):
        _safe_ui_call(loading_row.delete)


def _reset_form_state(state_manager) -> None:
    _safe_ui_call(state_manager.set_processing, False)
    _safe_ui_call(state_manager.set_input_enabled, True)


def _schedule_jobs_page_navigation() -> None:
    _safe_ui_call(ui.timer, 0.1, lambda: ui.navigate.to("/jobs"), once=True)


class JobSubmissionOrchestrator(BaseHandler):
    """Orchestrates job submission and progress tracking."""

    def __init__(self, form_handler: Any):
        super().__init__()
        self.form_handler = form_handler
        self.state_manager = getattr(form_handler, "state_manager", None)
        self.error_handler = FormErrorHandler()
        self.lifecycle = JobLifecycleService()

    async def submit_job(self, params: JobSubmitParams, **kwargs):
        return await self._execute_job(
            params.request_body,
            params.endpoint,
            params.task_schema,
            params.container,
            params.core,
            params.remaining_calls,
            params.conversation_id,
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
        self.state_manager = self.form_handler.state_manager
        self.state_manager.set_processing(True)

        form_element = kwargs.get("form_element")
        target_container, loading_row = self._prepare_loading_ui(
            container, endpoint, form_element
        )
        db_kwargs = {k: v for k, v in kwargs.items() if k not in ("form_element",)}
        pipeline_total = (1 + len(remaining_calls)) if remaining_calls else None

        job_id = await self._create_tracked_job(
            request_body,
            endpoint,
            task_schema,
            pipeline_total=pipeline_total,
            **db_kwargs,
        )
        if job_id and not remaining_calls:
            _schedule_jobs_page_navigation()
        if job_id:
            init_job_progress(job_id)

        background_tasks.create(
            self._background_submit(
                request_body=request_body,
                endpoint=endpoint,
                task_schema=task_schema,
                target_container=target_container,
                core=core,
                remaining_calls=remaining_calls,
                conversation_id=conversation_id,
                job_id=job_id,
                loading_row=loading_row,
            )
        )
        return True

    def _prepare_loading_ui(
        self, container, endpoint: str, form_element
    ) -> tuple[Any, Any]:
        target_container = form_element or container
        loading_row = None
        if not target_container:
            return target_container, loading_row
        with target_container:
            if form_element and hasattr(form_element, "clear"):
                form_element.clear()
            loading_row = render_loading_row(
                f"Processing {ToolRegistry.display_name_for_endpoint(endpoint)}..."
            )
        return target_container, loading_row

    async def _create_tracked_job(
        self,
        request_body,
        endpoint,
        task_schema,
        *,
        pipeline_total,
        **db_kwargs,
    ) -> str | None:
        return await self.lifecycle.create_tracked_job(
            request_body,
            endpoint,
            task_schema,
            pipeline_total_steps=pipeline_total,
            **db_kwargs,
        )

    async def _background_submit(
        self,
        *,
        request_body,
        endpoint,
        task_schema,
        target_container,
        core,
        remaining_calls,
        conversation_id,
        job_id,
        loading_row,
    ) -> None:
        poller: JobProgressPoller | None = None
        if job_id:
            poller = JobProgressPoller(job_id)
            poller.start()
        try:
            await self._run_successful_submit(
                request_body=request_body,
                endpoint=endpoint,
                task_schema=task_schema,
                target_container=target_container,
                core=core,
                remaining_calls=remaining_calls,
                conversation_id=conversation_id,
                job_id=job_id,
                loading_row=loading_row,
            )
        except UI_RENDER_ERRORS as e:
            await self._handle_submit_failure(
                e,
                job_id=job_id,
                conversation_id=conversation_id,
                endpoint=endpoint,
                loading_row=loading_row,
                target_container=target_container,
            )
        finally:
            if poller:
                await poller.stop()
            cleanup_job_progress(job_id)
            _reset_form_state(self.state_manager)

    async def _run_successful_submit(
        self,
        *,
        request_body,
        endpoint,
        task_schema,
        target_container,
        core,
        remaining_calls,
        conversation_id,
        job_id,
        loading_row,
    ) -> None:
        await self.lifecycle.record_job_started(
            conversation_id=conversation_id,
            endpoint=endpoint,
            job_id=job_id,
            request_body=request_body,
        )

        response_body = await core.submit_job(request_body, endpoint, job_id=job_id)

        await self.lifecycle.complete_successful_submission(
            job_id=job_id,
            response_body=response_body,
            conversation_id=conversation_id,
            endpoint=endpoint,
        )

        _delete_loading_row(loading_row)

        # Tracked single-step job: user was sent to /jobs; chat container is stale.
        if job_id and not remaining_calls:
            return

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
        except UI_RENDER_ERRORS as ui_err:
            self.logger.debug("UI update skipped (likely navigated away): %s", ui_err)

    async def _handle_submit_failure(
        self,
        exc: BaseException,
        *,
        job_id,
        conversation_id,
        endpoint,
        loading_row,
        target_container,
    ) -> None:
        self.logger.error("Job submission failed: %s", exc)
        message = str(exc)
        try:
            await self.lifecycle.mark_submission_failed(
                job_id=job_id,
                message=message,
                conversation_id=conversation_id,
                endpoint=endpoint,
            )
        except UI_RENDER_ERRORS as db_err:
            self.logger.error("Failed to persist submission failure: %s", db_err)
        _delete_loading_row(loading_row)
        if not job_id:
            try:
                if "demo_???" in message:
                    UIOperations.safe_notify(message, type="warning")
                else:
                    self.error_handler.display_error_boundary(
                        target_container, "Submission Failed", message
                    )
            except UI_RENDER_ERRORS as ui_err:
                self.logger.debug("Could not display error to UI: %s", ui_err)

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
        _ = task_schema
        job_id = job_info.get("job_id")

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
        pipeline = PipelineHandler(self)
        await pipeline.handle_remaining_calls(
            remaining_calls, response_body, container, core, **kwargs
        )

    def pipeline_handler(self):
        """Construct a pipeline handler bound to this orchestrator."""
        return PipelineHandler(self)
