"""
Job Database Module

This module provides SQLite database functionality for storing and managing jobs
in the RescueBox Desktop application. It mirrors the functionality from the
Electron codebase, storing job information including model/task IDs, request/response
data, and job status.

Jobs can be created from:
- Traditional model/task workflow (with modelUid/taskUid)
- Chatbot workflow (with endpoint name)

Usage:
    # Initialize database
    await init_database()

    # Create job
    job_db = JobDB()
    job = await job_db.create_job(
        model_uid='model_123',
        task_uid='task_456',
        request_body=request_body,
        task_schema=task_schema,
        endpoint='audio/transcribe'  # Optional, for chatbot jobs
    )

    # Update job status
    await job_db.update_job_status(job['uid'], JobStatus.Completed, response_body)

    # Get all jobs
    jobs = await job_db.get_all_jobs()
"""

import json
import logging
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from rb.api.models import RequestBody, ResponseBody, TaskSchema

from frontend.database.base_db import BaseDatabase
from frontend.database.db_exceptions import DB_ERRORS
from frontend.database.job_db_migrations import ensure_all_job_columns
from frontend.database.job_db_pipeline import (
    count_jobs_for_user,
    list_jobs_for_pipeline_root,
    update_pipeline_metadata_filter_criteria,
)
from frontend.database.job_db_queries import (
    fetch_all_jobs_for_current_user,
    fetch_job_by_uid,
)
from frontend.database.job_models import JobRecord, JobStatus
from frontend.database.schemas import (
    jobs_runtime_create_statements,
    jobs_runtime_index_statements,
)
from frontend.database.validation import DatabaseValidator
from frontend.utils.storage import get_user_id_for_jobs

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _try_ensure_columns(conn: sqlite3.Connection) -> None:
    try:
        ensure_all_job_columns(conn)
    except DB_ERRORS:
        logger.debug("Column migration encountered an error", exc_info=True)


class JobDB(BaseDatabase):
    """
    Job database manager for SQLite storage.

    Manages job records in SQLite database, supporting both traditional
    model/task jobs and chatbot endpoint-based jobs.
    """

    def __init__(self, db_path: Path | None = None):
        super().__init__(db_path, "jobs.db")
        self.validator = DatabaseValidator()

    def _create_schema(self) -> None:
        self._initialize_schema_sync()

    def _initialize_schema_sync(self) -> None:
        conn = self.connect()
        for statement in jobs_runtime_create_statements():
            conn.execute(statement.strip())
        for statement in jobs_runtime_index_statements():
            conn.execute(statement.strip())
        conn.commit()
        _try_ensure_columns(conn)

    async def initialize_schema(self):
        logger.info("Initializing database schema")
        self._initialize_schema_sync()
        logger.info("Database schema initialized successfully")

    async def create_job(
        self,
        request_body: RequestBody | dict[str, Any],
        task_schema: TaskSchema | dict[str, Any],
        model_uid: str | None = None,
        task_uid: str | None = None,
        endpoint: str | None = None,
        case_notes: str | None = None,
        user_id: str | None = None,
        endpoint_chain: list[str] | None = None,
        pipeline_root_job_id: str | None = None,
        pipeline_total_steps: Any | None = None,
    ) -> JobRecord:
        if not model_uid and not endpoint:
            raise ValueError("Either model_uid/task_uid or endpoint must be provided")

        if user_id is None:
            try:
                user_id = get_user_id_for_jobs()
            except DB_ERRORS:
                user_id = None

        start_time = datetime.now().isoformat()
        uid = f"JOB_{uuid.uuid4().hex[:6]}"
        conn = self.connect()
        _try_ensure_columns(conn)

        try:
            maybe_filter_id = None
            if isinstance(request_body, dict):
                params_section = request_body.get("parameters") or {}
                if isinstance(params_section, dict):
                    maybe_filter_id = params_section.get("filterId") or (
                        params_section.get("_meta") or {}
                    ).get("filterId")
            else:
                params_section = getattr(request_body, "parameters", None) or {}
                if isinstance(params_section, dict):
                    maybe_filter_id = params_section.get("filterId") or (
                        params_section.get("_meta") or {}
                    ).get("filterId")
        except DB_ERRORS:
            maybe_filter_id = None

        chain: list[str] | None = None
        if endpoint_chain:
            chain = [str(x) for x in endpoint_chain]
        elif endpoint:
            chain = [endpoint]

        stored_pipeline_root: str | None = None
        if pipeline_root_job_id and str(pipeline_root_job_id).strip():
            stored_pipeline_root = str(pipeline_root_job_id).strip()
        elif pipeline_total_steps is not None:
            try:
                if int(pipeline_total_steps) > 1:
                    stored_pipeline_root = uid
            except (TypeError, ValueError):
                pass

        job_record = JobRecord(
            uid=uid,
            userId=user_id,
            modelUid=model_uid,
            taskUid=task_uid,
            endpoint=endpoint,
            endpointChain=chain,
            pipelineRootJobId=stored_pipeline_root,
            filterId=maybe_filter_id,
            caseNotes=case_notes or None,
            startTime=start_time,
            endTime=None,
            status=JobStatus.RUNNING,
            statusText=None,
            request=request_body,
            response=None,
            taskSchema=task_schema,
        )

        job_data = job_record.model_dump_for_db()

        logger.debug(
            "Creating job %s (model_uid=%s, task_uid=%s, endpoint=%s)",
            uid,
            model_uid,
            task_uid,
            endpoint,
        )

        insert_sql = """
            INSERT INTO jobs (uid, userId, modelUid, taskUid, endpoint, endpointChain, pipelineRootJobId,
                            pipelineMetadataFilterCriteria, startTime, endTime, status, statusText, request,
                            response, taskSchema, filterId, caseNotes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            job_data["uid"],
            job_data.get("userId"),
            job_data["modelUid"],
            job_data["taskUid"],
            job_data["endpoint"],
            job_data.get("endpointChain"),
            job_data.get("pipelineRootJobId"),
            job_data.get("pipelineMetadataFilterCriteria"),
            job_data["startTime"],
            job_data["endTime"],
            job_data["status"],
            job_data["statusText"],
            job_data["request"],
            job_data["response"],
            job_data["taskSchema"],
            job_data.get("filterId"),
            job_data.get("caseNotes"),
        )

        max_attempts = 6
        attempt = 0
        backoff = 0.05
        while attempt < max_attempts:
            try:
                conn.execute(insert_sql, params)
                conn.commit()
                logger.debug("Job %s created successfully", uid)
                return await self.get_job_by_uid(uid)
            except sqlite3.IntegrityError as e:
                logger.warning("Job ID collision detected when creating %s: %s", uid, e)
                uid = f"JOB_{uuid.uuid4().hex}"
                job_data["uid"] = uid
                params = list(params)
                params[0] = uid
                params = tuple(params)
                attempt += 1
                continue
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    logger.warning(
                        "Database locked when creating job %s, retrying (attempt=%d): %s",
                        uid,
                        attempt + 1,
                        e,
                    )
                    time.sleep(backoff)
                    backoff = min(1.0, backoff * 2)
                    attempt += 1
                    continue
                raise

        logger.error(
            "Failed to create job after %d attempts for uid %s", max_attempts, uid
        )
        raise RuntimeError("Failed to create job due to database errors")

    def get_job_by_uid_sync(self, uid: str) -> JobRecord | None:
        conn = self.connect()
        _try_ensure_columns(conn)
        return fetch_job_by_uid(conn, uid, enforce_user_scope=True)

    async def get_job_by_uid(self, uid: str) -> JobRecord | None:
        return self.get_job_by_uid_sync(uid)

    async def get_all_jobs(self) -> list[dict[str, Any]]:
        conn = self.connect()
        _try_ensure_columns(conn)
        return fetch_all_jobs_for_current_user(conn)

    async def list_jobs_for_pipeline_root(
        self, user_id: str, root_uid: str
    ) -> list[JobRecord]:
        conn = self.connect()
        return list_jobs_for_pipeline_root(conn, user_id, root_uid)

    async def update_job_pipeline_metadata_filter_criteria(
        self, uid: str, criteria: str
    ) -> bool:
        conn = self.connect()
        return update_pipeline_metadata_filter_criteria(conn, uid, criteria)

    def get_job_count_for_user(self, user_id: str | None) -> int:
        return count_jobs_for_user(self.connect(), user_id)

    async def update_job_status(
        self,
        uid: str,
        status: JobStatus,
        response_body: ResponseBody | dict[str, Any] | None = None,
        status_text: str | None = None,
        end_time: datetime | None = None,
    ) -> bool:
        conn = self.connect()
        if isinstance(status, str):
            for s in JobStatus:
                if s.value.lower() == status.lower():
                    status = s
                    break
        status_val = status.value if hasattr(status, "value") else status
        logger.debug("Updating job %s status to %s", uid, status_val)

        if end_time is None:
            end_time = datetime.now()

        updates = {"status": status_val, "endTime": end_time.isoformat()}

        if response_body is not None:
            if isinstance(response_body, ResponseBody):
                updates["response"] = json.dumps(response_body.model_dump(mode="json"))
            else:
                updates["response"] = json.dumps(response_body)

        if status_text is not None:
            updates["statusText"] = status_text

        set_clause = ", ".join([f"{k} = ?" for k in updates])
        values = list(updates.values()) + [uid]

        cursor = conn.execute(f"UPDATE jobs SET {set_clause} WHERE uid = ?", values)
        conn.commit()

        if cursor.rowcount > 0:
            logger.debug("Job %s updated successfully", uid)
            return True
        logger.warning("Job %s not found for update", uid)
        return False

    async def update_job_status_text(self, uid: str, status_text: str) -> bool:
        """Update ``statusText`` only (for Running progress polls)."""
        conn = self.connect()
        cursor = conn.execute(
            "UPDATE jobs SET statusText = ? WHERE uid = ?",
            (status_text, uid),
        )
        conn.commit()
        if cursor.rowcount > 0:
            return True
        logger.warning("Job %s not found for statusText update", uid)
        return False

    async def disassociate_job_from_case(self, uid: str) -> bool:
        conn = self.connect()
        logger.info("Disassociating job %s from case", uid)
        cursor = conn.execute("UPDATE jobs SET userId = NULL WHERE uid = ?", (uid,))
        conn.commit()
        return cursor.rowcount > 0

    async def delete_job(self, uid: str) -> bool:
        conn = self.connect()
        logger.info("Deleting job %s", uid)

        cursor = conn.execute("DELETE FROM jobs WHERE uid = ?", (uid,))
        conn.commit()

        if cursor.rowcount > 0:
            logger.info("Job %s deleted successfully", uid)
            return True
        logger.warning("Job %s not found for deletion", uid)
        return False


_JOB_DB_SINGLETON: dict[str, JobDB | None] = {"instance": None}


async def init_database(db_path: Path | None = None) -> JobDB:
    if _JOB_DB_SINGLETON["instance"] is None:
        _JOB_DB_SINGLETON["instance"] = JobDB(db_path)
        await _JOB_DB_SINGLETON["instance"].initialize_schema()

    return _JOB_DB_SINGLETON["instance"]


def get_job_db() -> JobDB:
    if _JOB_DB_SINGLETON["instance"] is None:
        logger.debug("Lazy-initializing job database")
        _JOB_DB_SINGLETON["instance"] = JobDB()
        _JOB_DB_SINGLETON["instance"]._initialize_schema_sync()

    return _JOB_DB_SINGLETON["instance"]
