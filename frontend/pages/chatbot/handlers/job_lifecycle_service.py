"""Database/history lifecycle helpers for job submission flow."""

from __future__ import annotations

import logging
from typing import Any, Optional

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.pages.chatbot.database_service import DatabaseService
from frontend.utils import get_user_id_for_jobs

logger = logging.getLogger(__name__)


class JobLifecycleService:
    """Isolate DB/history side-effects from UI orchestration code."""

    async def create_tracked_job(
        self,
        request_body: Any,
        endpoint: str,
        task_schema: Any,
        *,
        pipeline_total_steps: Optional[int],
        **db_kwargs: Any,
    ) -> Optional[str]:
        try:
            job_record = await DatabaseService.create_and_track_job(
                request_body,
                endpoint,
                task_schema,
                user_id=get_user_id_for_jobs(),
                pipeline_total_steps=pipeline_total_steps,
                **db_kwargs,
            )
            if job_record:
                return job_record.get("job_id")
        except UI_RENDER_ERRORS as e:
            logger.error("Failed to create and track job in DB: %s", e)
        return None

    async def record_job_started(
        self,
        *,
        conversation_id: Optional[str],
        endpoint: str,
        job_id: Optional[str],
        request_body: Any,
    ) -> None:
        if conversation_id and job_id:
            await DatabaseService.save_job_started_to_history(
                conversation_id,
                endpoint,
                job_id,
                request_body=request_body,
            )

    async def complete_successful_submission(
        self,
        *,
        job_id: Optional[str],
        response_body: Any,
        conversation_id: Optional[str],
        endpoint: str,
    ) -> None:
        if job_id:
            await DatabaseService.complete_job(job_id, response_body)
        if conversation_id:
            await DatabaseService.save_tool_result_to_history(
                conversation_id, endpoint, job_id
            )

    async def mark_submission_failed(
        self,
        *,
        job_id: Optional[str],
        message: str,
        conversation_id: Optional[str],
        endpoint: str,
    ) -> None:
        if job_id:
            await DatabaseService.update_job_status(
                job_uid=job_id,
                status="Failed",
                status_text=message,
            )
        if conversation_id:
            await DatabaseService.save_error_to_history(
                conversation_id, endpoint, message
            )
