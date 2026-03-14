"""
Job Manager.

Handles job creation, database operations, and status updates.
"""

import logging
from frontend.database import JobStatus
from frontend.database.job_db import get_job_db
from frontend.utils.logging_context import set_logging_context


logger = logging.getLogger(__name__)


class JobManager:
    """Handles job creation, database operations, and status updates."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def get_job_database(self):
        """Get job database instance."""
        return get_job_db()

    async def create_job_record(self, job_db, request_body, task_schema, endpoint):
        """
        Create job record in database.

        Args:
            job_db: Job database instance
            request_body: Request body
            task_schema: Task schema
            endpoint: API endpoint

        Returns:
            Job record
        """
        job = await job_db.create_job(
            request_body=request_body,
            task_schema=task_schema,
            endpoint=endpoint
        )

        # Set logging context for this job
        set_logging_context(
            job_id=job.uid,
            model_id=getattr(job, 'model_uid', None),
            session_id=None  # Could be conversation_id if available
        )

        self.logger.info("Job %s created in database", job.uid)
        return job

    async def update_job_status_completed(self, job_uid: str, response_body):
        """
        Update job status to completed.

        Args:
            job_uid: Job UID
            response_body: Response body
        """
        job_db = get_job_db()
        await job_db.update_job_status(
            uid=job_uid,
            status=JobStatus.COMPLETED,
            response_body=response_body
        )
        self.logger.info("Job %s updated to Completed status", job_uid)

    async def update_job_status_failed(self, job_uid: str, error_message: str = None):
        """
        Update job status to failed.

        Args:
            job_uid: Job UID
            error_message: Optional error message
        """
        job_db = get_job_db()
        await job_db.update_job_status(
            uid=job_uid,
            status=JobStatus.FAILED,
            status_text=error_message
        )
        self.logger.info("Job %s updated to Failed status", job_uid)
