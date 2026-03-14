"""
Database Service.

Unified database operations service with consistent error handling.
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any

from frontend.database import JobStatus, get_chat_history_db
from frontend.database.job_db import get_job_db
from frontend.utils.logging_context import set_logging_context

from frontend.pages.chatbot.utils.message_service import MessageService

logger = logging.getLogger(__name__)


class DatabaseService:
    """Unified database operations service with consistent error handling."""

    @staticmethod
    async def save_message_to_history(conversation_id: str, role: str, content: str, **kwargs):
        """Save message with consistent error handling."""
        for attempt in range(5):
            try:
                chat_history = get_chat_history_db()
                await chat_history.add_message(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    **kwargs
                )
                logger.debug("Message saved to history: %s", conversation_id)
                return
            except Exception as e:
                if "locked" in str(e).lower() and attempt < 4:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                logger.error("Failed to save message to history: %s", str(e))
                # Don't raise - chat history failures shouldn't break main flow
                break

    @staticmethod
    async def save_tool_call_to_history(conversation_id: str, endpoint: str, arguments: dict):
        """Save tool call with consistent formatting."""
        try:
            chat_history = get_chat_history_db()

            # Serialize arguments consistently
            serialized_args = MessageService.serialize_arguments(arguments)

            await chat_history.add_message(
                conversation_id=conversation_id,
                role='assistant',
                content=f"Selected tool: {endpoint}",
                message_type='tool_call',
                tool_calls=[{
                    'name': endpoint,
                    'arguments': serialized_args
                }]
            )
            logger.debug("Tool call saved to history: %s", endpoint)
        except Exception as e:
            logger.error("Failed to save tool call to history: %s", str(e))

    @staticmethod
    async def save_job_started_to_history(conversation_id: str, endpoint: str, job_id: str):
        """Save a job-started marker into chat history so UI can recover running jobs."""
        try:
            chat_history = get_chat_history_db()
            await chat_history.add_message(
                conversation_id=conversation_id,
                role='assistant',
                content=f"Job {job_id} started for {endpoint}",
                message_type='tool_result',
                tool_call_endpoint=endpoint,
                metadata={'job_id': job_id, 'status': 'RUNNING'}
            )
            logger.debug("Job started saved to history: %s (conv: %s)", job_id, conversation_id)
        except Exception as e:
            logger.error("Failed to save job-started to history: %s", str(e))

    @staticmethod
    async def save_tool_result_to_history(conversation_id: str, endpoint: str, job_id: Optional[str] = None):
        """Save tool result with consistent formatting."""
        for attempt in range(10):
            try:
                chat_history = get_chat_history_db()

                content = f"Job {job_id} completed successfully" if job_id else "Job completed successfully"
                await chat_history.add_message(
                    conversation_id=conversation_id,
                    role='assistant',
                    content=content,
                    message_type='tool_result',
                    tool_call_endpoint=endpoint,
                    metadata={'job_id': job_id, 'status': 'completed'} if job_id else {'status': 'completed'}
                )
                logger.debug("Tool result saved to history: %s", endpoint)
                return
            except Exception as e:
                if "locked" in str(e).lower() and attempt < 9:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                logger.error("Failed to save tool result to history: %s", str(e))
                break

    @staticmethod
    async def save_error_to_history(conversation_id: str, endpoint: str, error_message: str, raw_error: Optional[str] = None):
        """Save error message with consistent formatting."""
        try:
            chat_history = get_chat_history_db()

            metadata = {'status': 'failed'}
            if raw_error:
                metadata['error'] = raw_error

            await chat_history.add_message(
                conversation_id=conversation_id,
                role='assistant',
                content=error_message,
                message_type='error',
                tool_call_endpoint=endpoint,
                metadata=metadata
            )
            logger.debug("Error message saved to history: %s", endpoint)
        except Exception as e:
            logger.error("Failed to save error to history: %s", str(e))

    @staticmethod
    async def create_and_track_job(request_body, endpoint: str, task_schema=None, response_body=None) -> Optional[Dict[str, Any]]:
        """Create job and return tracking info."""
        for attempt in range(3):
            try:
                job_db = get_job_db()

                # Ensure request_body is serializable
                if hasattr(request_body, 'model_dump'):
                    job_request_body = request_body.model_dump()
                else:
                    job_request_body = request_body

                # Ensure task_schema is serializable
                if task_schema and hasattr(task_schema, 'model_dump'):
                    job_task_schema = task_schema.model_dump()
                else:
                    job_task_schema = task_schema or {}

                job_record = await job_db.create_job(
                    request_body=job_request_body,
                    task_schema=job_task_schema,
                    endpoint=endpoint
                )

                # Set logging context for this job
                set_logging_context(
                    job_id=job_record.uid,
                    model_id=getattr(job_record, 'modelUid', None),
                    session_id=None  # Could be set from conversation context if available
                )

                # Set final status and store response
                final_status = JobStatus.COMPLETED if response_body is not None else JobStatus.RUNNING

                # Ensure response_body is serializable
                job_response_body = None
                if response_body is not None:
                    try:
                        if hasattr(response_body, 'model_dump'):
                            job_response_body = response_body.model_dump(mode='json')
                        else:
                            job_response_body = response_body
                        # Test serialization
                        json.dumps(job_response_body)
                    except (TypeError, ValueError) as e:
                        logger.warning("Response body not serializable, storing without response: %s", str(e))
                        job_response_body = None

                await job_db.update_job_status(
                    uid=job_record.uid,
                    status=final_status,
                    response_body=job_response_body
                )

                logger.info("Job created and completed: %s (status: %s)", job_record.uid, final_status.value)
                return {
                    'job_id': job_record.uid,
                    'status': final_status.value
                }

            except Exception as e:
                if "locked" in str(e).lower() and attempt < 2:
                    await asyncio.sleep(0.5)
                    continue
                if "UNIQUE constraint failed" in str(e):
                    logger.error("Job ID collision detected: %s. The database might be out of sync with the ID generator.", str(e))
                else:
                    logger.error("Failed to create and track job: %s", str(e))
                return None

    @staticmethod
    async def complete_job(job_uid: str, response_body) -> bool:
        """Mark job as completed with response data."""
        for attempt in range(3):
            try:
                job_db = get_job_db()

                # Ensure response_body is serializable
                try:
                    if hasattr(response_body, 'model_dump'):
                        job_response_body = response_body.model_dump(mode='json')
                    else:
                        job_response_body = response_body

                    # Test serialization
                    json.dumps(job_response_body)

                    await job_db.update_job_status(
                        uid=job_uid,
                        status=JobStatus.COMPLETED,
                        response_body=job_response_body
                    )
                except (TypeError, ValueError) as e:
                    logger.warning("Response body not serializable, updating job status without response: %s", str(e))
                    await job_db.update_job_status(
                        uid=job_uid,
                        status=JobStatus.COMPLETED,
                        response_body=None
                    )

                logger.debug("Job marked as completed: %s", job_uid)
                return True

            except Exception as e:
                if "locked" in str(e).lower() and attempt < 2:
                    await asyncio.sleep(0.5)
                    continue
                logger.error("Failed to complete job: %s", str(e))
                return False

    @staticmethod
    async def update_job_status(job_uid: str, status: str, **kwargs):
        """Update job status with consistent error handling."""
        for attempt in range(3):
            try:
                job_db = get_job_db()
                # Normalize status to JobStatus enum if a string was provided
                status_enum = status
                if isinstance(status, str):
                    try:
                        status_enum = JobStatus(status)
                    except ValueError:
                        # case-insensitive match against enum values
                        matched = None
                        for s in JobStatus:
                            if s.value.lower() == status.lower():
                                matched = s
                                break
                        status_enum = matched or JobStatus.RUNNING

                await job_db.update_job_status(
                    uid=job_uid,
                    status=status_enum,
                    **kwargs
                )
                logger.debug("Job status updated: %s -> %s", job_uid, status)
                return
            except Exception as e:
                if "locked" in str(e).lower() and attempt < 2:
                    await asyncio.sleep(0.5)
                    continue
                logger.error("Failed to update job status: %s", str(e))
                break
