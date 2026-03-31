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
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import uuid
from pydantic import BaseModel, Field, field_validator
import time

# Import backend models for type hints and validation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from rb.api.models import TaskSchema, RequestBody, ResponseBody

# Import refactored components
from frontend.database.base_db import BaseDatabase
from frontend.database.schemas import JobDatabaseSchema, SchemaManager
from frontend.database.validation import DatabaseValidator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class JobStatus(str, Enum):
    """Job status enumeration"""
    RUNNING = 'Running'
    COMPLETED = 'Completed'
    FAILED = 'Failed'
    CANCELED = 'Canceled'


class JobRecord(BaseModel):
    """
    Pydantic model for job records in the database.
    
    Represents a job with all its metadata, request, response, and schema.
    Supports both traditional model/task jobs and chatbot endpoint-based jobs.
    
    Attributes:
        uid (str): Unique job identifier
        modelUid (Optional[str]): Model UID (for traditional jobs)
        taskUid (Optional[str]): Task UID (for traditional jobs)
        endpoint (Optional[str]): Endpoint name (for chatbot jobs)
        startTime (str): Job start time in ISO format
        endTime (Optional[str]): Job end time in ISO format
        status (JobStatus): Job status
        statusText (Optional[str]): Status text (for errors)
        request (Union[RequestBody, Dict]): Request body (validated as RequestBody)
        response (Optional[Union[ResponseBody, Dict]]): Response body (validated as ResponseBody)
        taskSchema (Union[TaskSchema, Dict]): Task schema (validated as TaskSchema)
    
    Tips:
    - request, response, and taskSchema can be dicts or Pydantic models
    - When loaded from database, they are dicts (validated on access)
    - When creating, can pass Pydantic models directly
    """
    
    uid: str = Field(..., description="Unique job identifier")
    userId: Optional[str] = Field(None, description="NiceGUI session or user identifier")
    modelUid: Optional[str] = Field(None, description="Model UID for traditional jobs")
    taskUid: Optional[str] = Field(None, description="Task UID for traditional jobs")
    endpoint: Optional[str] = Field(None, description="Endpoint name for chatbot jobs")
    endpointChain: Optional[List[str]] = Field(
        None, description="Ordered endpoints for multi-step chatbot pipelines (includes current job endpoint)"
    )
    filterId: Optional[str] = Field(None, description="Optional persisted filter id linking to file_filters")
    caseNotes: Optional[str] = Field(None, description="User-entered case notes for the job")
    startTime: str = Field(..., description="Job start time in ISO format")
    endTime: Optional[str] = Field(None, description="Job end time in ISO format")
    status: JobStatus = Field(..., description="Job status")
    statusText: Optional[str] = Field(None, description="Status text for errors")
    request: Union[RequestBody, Dict[str, Any]] = Field(..., description="Request body")
    response: Optional[Union[ResponseBody, Dict[str, Any]]] = Field(None, description="Response body")
    taskSchema: Union[TaskSchema, Dict[str, Any]] = Field(..., description="Task schema")
    
    @field_validator('request', mode='before')
    @classmethod
    def validate_request(cls, v):
        """Convert dict to RequestBody if needed"""
        if isinstance(v, dict):
            try:
                return RequestBody(**v)
            except Exception as e:
                logger.warning("Could not validate request as RequestBody, keeping as dict: %s", e)
                return v
        return v
    
    @field_validator('response', mode='before')
    @classmethod
    def validate_response(cls, v):
        """Convert dict to ResponseBody if needed"""
        if v is None:
            return None
        if isinstance(v, dict):
            try:
                return ResponseBody(**v)
            except Exception as e:
                logger.warning("Could not validate response as ResponseBody, keeping as dict: %s", e)
                return v
        return v
    
    @field_validator('taskSchema', mode='before')
    @classmethod
    def validate_task_schema(cls, v):
        """Convert dict to TaskSchema if needed"""
        if isinstance(v, dict):
            try:
                return TaskSchema(**v)
            except Exception as e:
                logger.warning("Could not validate taskSchema as TaskSchema, keeping as dict: %s", e)
                return v
        return v

    @field_validator('endpointChain', mode='before')
    @classmethod
    def validate_endpoint_chain(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, list):
            return [str(x) for x in v]
        if isinstance(v, str):
            try:
                data = json.loads(v)
                return [str(x) for x in data] if isinstance(data, list) else None
            except json.JSONDecodeError:
                return None
        return None

    @field_validator('status', mode='before')
    @classmethod
    def validate_status(cls, v):
        """Convert string to JobStatus if needed"""
        if isinstance(v, str):
            try:
                return JobStatus(v)
            except ValueError:
                # Try to match case-insensitively
                for status in JobStatus:
                    if status.value.lower() == v.lower():
                        return status
                logger.warning("Unknown status: %s, using RUNNING", v)
                return JobStatus.RUNNING
        return v
    
    def model_dump_for_db(self) -> Dict[str, Any]:
        """
        Convert JobRecord to dict for database storage.

        Returns:
            Dict with JSON-serialized request, response, and taskSchema

        Tips:
        - Converts Pydantic models to dicts
        - Serializes complex fields to JSON strings for database
        """
        data = self.model_dump(mode='json')

        # Use DatabaseValidator for consistent serialization
        validator = DatabaseValidator()

        # Serialize complex fields to JSON strings for database
        data['request'] = validator.serialize_json(data.get('request'))
        data['response'] = validator.serialize_json(data.get('response')) if data.get('response') else None
        data['taskSchema'] = validator.serialize_json(data.get('taskSchema'))

        # Convert enum to string
        if isinstance(data.get('status'), JobStatus):
            data['status'] = data['status'].value
        # Ensure optional fields are present (may be None)
        if 'filterId' not in data:
            data['filterId'] = None
        if 'caseNotes' not in data:
            data['caseNotes'] = None
        if data.get('endpointChain') is not None:
            data['endpointChain'] = json.dumps(data['endpointChain'])
        else:
            data['endpointChain'] = None

        return data
    
    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True
        use_enum_values = True


class JobDB(BaseDatabase):
    """
    Job database manager for SQLite storage.
    
    Manages job records in SQLite database, supporting both traditional
    model/task jobs and chatbot endpoint-based jobs.
    
    Attributes:
        db_path (Path): Path to SQLite database file
        conn (sqlite3.Connection): Database connection
    
    Tips:
    - Database file is stored in frontend/data/jobs.db
    - Jobs are stored with JSON serialization for request/response/taskSchema
    - Supports both modelUid/taskUid and endpoint-based jobs
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize JobDB.

        Args:
            db_path (Optional[Path]): Path to database file.
                Defaults to frontend/data/jobs.db if not provided
        """
        super().__init__(db_path, "jobs.db")

        # Initialize schema manager
        schema = JobDatabaseSchema()
        self.schema_manager = SchemaManager(schema)

        # Initialize validator
        self.validator = DatabaseValidator()

    def _create_schema(self) -> None:
        """
        Create database schema for jobs.

        This method is called by the base class during connection.
        """
        self.schema_manager.create_schema(self.conn)

    def _ensure_userid_column(self, conn: sqlite3.Connection) -> None:
        """
        Ensure the `userId` column exists on the jobs table.

        If the column is missing (older DB), add it and create the index.
        This makes upgrades from older DB files transparent at runtime.
        """
        try:
            # Quick check whether the column exists
            conn.execute("SELECT userId FROM jobs LIMIT 1")
        except sqlite3.OperationalError as e:
            if 'no such column' in str(e).lower():
                logger.info("userId column missing in jobs table; adding column")
                try:
                    conn.execute("ALTER TABLE jobs ADD COLUMN userId TEXT")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_userId ON jobs(userId)")
                    conn.commit()
                    logger.info("Added userId column and index to jobs table")
                except Exception as e_add:
                    logger.exception("Failed to add userId column to jobs table: %s", e_add)
                    raise
            else:
                # Other operational errors should be propagated
                raise

    def _ensure_caseNotes_column(self, conn: sqlite3.Connection) -> None:
        """Ensure the `caseNotes` column exists (migration for older DBs)."""
        try:
            conn.execute("SELECT caseNotes FROM jobs LIMIT 1")
        except sqlite3.OperationalError as e:
            if 'no such column' in str(e).lower():
                logger.info("caseNotes column missing; adding column")
                try:
                    conn.execute("ALTER TABLE jobs ADD COLUMN caseNotes TEXT")
                    conn.commit()
                    logger.info("Added caseNotes column to jobs table")
                except Exception as e_add:
                    logger.exception("Failed to add caseNotes column: %s", e_add)
                    raise
            else:
                raise

    def _ensure_endpoint_chain_column(self, conn: sqlite3.Connection) -> None:
        """Ensure `endpointChain` JSON column exists (multi-step chatbot jobs)."""
        try:
            conn.execute("SELECT endpointChain FROM jobs LIMIT 1")
        except sqlite3.OperationalError as e:
            if 'no such column' in str(e).lower():
                logger.info("endpointChain column missing; adding column")
                try:
                    conn.execute("ALTER TABLE jobs ADD COLUMN endpointChain TEXT")
                    conn.commit()
                    logger.info("Added endpointChain column to jobs table")
                except Exception as e_add:
                    logger.exception("Failed to add endpointChain column: %s", e_add)
                    raise
            else:
                raise

    def connect(self) -> sqlite3.Connection:
        """
        Connect to SQLite database.

        Returns:
            sqlite3.Connection: Database connection

        Note:
            Schema initialization is handled by the base class
        """
        return super().connect()
    
    def close(self):
        """
        Close database connection.
        
        Returns:
            None
        """
        if self.conn:
            logger.debug("Closing database connection")
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")
    
    async def initialize_schema(self):
        """
        Initialize database schema (create jobs table if it doesn't exist).
        
        Returns:
            None
        
        Tips:
        - Creates jobs table with all required fields
        - Uses TEXT for JSON fields (request, response, taskSchema)
        - Supports both modelUid/taskUid and endpoint-based jobs
        """
        conn = self.connect()
        logger.info("Initializing database schema")
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                uid TEXT PRIMARY KEY,
                userId TEXT,
                modelUid TEXT,
                taskUid TEXT,
                endpoint TEXT,
                startTime TEXT NOT NULL,
                endTime TEXT,
                status TEXT NOT NULL,
                statusText TEXT,
                request TEXT NOT NULL,
                response TEXT,
                taskSchema TEXT NOT NULL,
                filterId TEXT,
                caseNotes TEXT
            )
        """)
        
        # Create indexes for common queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_modelUid ON jobs(modelUid)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_userId ON jobs(userId)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_startTime ON jobs(startTime)")
        conn.execute("CREATE INDEX IF NOT EXISTS filterID ON jobs(filterId)")
        
        conn.commit()
        logger.info("Database schema initialized successfully")
        # Ensure userId and caseNotes columns exist for older DBs
        try:
            self._ensure_userid_column(conn)
            self._ensure_caseNotes_column(conn)
            self._ensure_endpoint_chain_column(conn)
        except Exception:
            logger.debug("Column migration encountered an error during initialization")
    
    async def create_job(
        self,
        request_body: Union[RequestBody, Dict[str, Any]],
        task_schema: Union[TaskSchema, Dict[str, Any]],
        model_uid: Optional[str] = None,
        task_uid: Optional[str] = None,
        endpoint: Optional[str] = None,
        case_notes: Optional[str] = None,
        user_id: Optional[str] = None,
        endpoint_chain: Optional[List[str]] = None,
    ) -> JobRecord:
        """
        Create a new job record.
        
        Args:
            request_body (Union[RequestBody, Dict[str, Any]]): Request body (inputs and parameters).
                Can be RequestBody Pydantic model or dict
            task_schema (Union[TaskSchema, Dict[str, Any]]): Task schema at time of job creation.
                Can be TaskSchema Pydantic model or dict
            model_uid (Optional[str]): Model UID (for traditional jobs)
            task_uid (Optional[str]): Task UID (for traditional jobs)
            endpoint (Optional[str]): Endpoint name (for chatbot jobs)
        
        Returns:
            JobRecord: Created job record as Pydantic model
        
        Raises:
            ValueError: If neither (model_uid/task_uid) nor endpoint is provided
        
        Tips:
        - Generates job uid as JOB_<uuid_hex> for consistency
        - Stores request_body and task_schema as JSON strings in database
        - Initial status is 'Running'
        - At least one of (model_uid/task_uid) or endpoint must be provided
        - Accepts both Pydantic models and dicts for backward compatibility
        """
        if not model_uid and not endpoint:
            raise ValueError("Either model_uid/task_uid or endpoint must be provided")
        
        # Use explicit user_id if passed (from request context), else resolve from storage
        if user_id is None:
            try:
                from frontend.utils.nicegui_storage import get_user_id_for_jobs
                user_id = get_user_id_for_jobs()
            except Exception:
                user_id = None

        # Generate job uid consistently as JOB_<uuid_hex>
        start_time = datetime.now().isoformat()
        uid = f"JOB_{uuid.uuid4().hex[:6]}"
        conn = self.connect()
        # Ensure userId and caseNotes columns exist for older DBs
        try:
            self._ensure_userid_column(conn)
            self._ensure_caseNotes_column(conn)
            self._ensure_endpoint_chain_column(conn)
        except Exception:
            logger.debug("Failed to ensure columns before insert")
        
        # Create JobRecord with validation
        # Extract optional filterId from request body parameters (supports _meta convention)
        try:
            maybe_filter_id = None
            if isinstance(request_body, dict):
                params_section = request_body.get('parameters') or {}
                if isinstance(params_section, dict):
                    # prefer top-level filterId for backward-compat, else look in _meta
                    maybe_filter_id = params_section.get('filterId') or (params_section.get('_meta') or {}).get('filterId')
            else:
                # pydantic model case
                params_section = getattr(request_body, 'parameters', None) or {}
                if isinstance(params_section, dict):
                    maybe_filter_id = params_section.get('filterId') or (params_section.get('_meta') or {}).get('filterId')
        except Exception:
            maybe_filter_id = None

        chain: Optional[List[str]] = None
        if endpoint_chain:
            chain = [str(x) for x in endpoint_chain]
        elif endpoint:
            chain = [endpoint]

        job_record = JobRecord(
            uid=uid,
            userId=user_id,
            modelUid=model_uid,
            taskUid=task_uid,
            endpoint=endpoint,
            endpointChain=chain,
            filterId=maybe_filter_id,
            caseNotes=case_notes or None,
            startTime=start_time,
            endTime=None,
            status=JobStatus.RUNNING,
            statusText=None,
            request=request_body,  # Will be validated by JobRecord
            response=None,
            taskSchema=task_schema  # Will be validated by JobRecord
        )
        
        # Convert to database format
        job_data = job_record.model_dump_for_db()
        
        logger.info("Creating job %s (model_uid=%s, task_uid=%s, endpoint=%s)", uid, model_uid, task_uid, endpoint)

        insert_sql = """
            INSERT INTO jobs (uid, userId, modelUid, taskUid, endpoint, endpointChain, startTime, endTime,
                            status, statusText, request, response, taskSchema, filterId, caseNotes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            job_data['uid'],
            job_data.get('userId'),
            job_data['modelUid'],
            job_data['taskUid'],
            job_data['endpoint'],
            job_data.get('endpointChain'),
            job_data['startTime'],
            job_data['endTime'],
            job_data['status'],
            job_data['statusText'],
            job_data['request'],
            job_data['response'],
            job_data['taskSchema'],
            job_data.get('filterId'),
            job_data.get('caseNotes')
        )

        # Try inserting with handling for IntegrityError and transient locking
        max_attempts = 6
        attempt = 0
        backoff = 0.05
        while attempt < max_attempts:
            try:
                conn.execute(insert_sql, params)
                conn.commit()
                logger.info("Job %s created successfully", uid)
                return await self.get_job_by_uid(uid)
            except sqlite3.IntegrityError as e:
                # UID collision - generate new UID and retry a few times
                logger.warning("Job ID collision detected when creating %s: %s", uid, e)
                # regenerate uid using uuid4 to avoid repeated collisions
                uid = f"JOB_{uuid.uuid4().hex}"
                job_data['uid'] = uid
                params = list(params)
                params[0] = uid
                params = tuple(params)
                attempt += 1
                continue
            except sqlite3.OperationalError as e:
                # Handle transient "database is locked" errors with backoff
                if 'locked' in str(e).lower():
                    logger.warning("Database locked when creating job %s, retrying (attempt=%d): %s", uid, attempt + 1, e)
                    time.sleep(backoff)
                    backoff = min(1.0, backoff * 2)
                    attempt += 1
                    continue
                raise

        # If we reach here, raise an error
        logger.error("Failed to create job after %d attempts for uid %s", max_attempts, uid)
        raise RuntimeError("Failed to create job due to database errors")
    
    async def get_job_by_uid(self, uid: str) -> Optional[JobRecord]:
        """
        Get job by UID.
        
        Args:
            uid (str): Job UID
        
        Returns:
            Optional[JobRecord]: Job record as Pydantic model if found, None otherwise
        
        Tips:
        - Parses JSON fields (request, response, taskSchema) and validates as Pydantic models
        - Returns JobRecord with validated RequestBody, ResponseBody, and TaskSchema
        """
        conn = self.connect()
        # Ensure columns exist for older DBs
        try:
            self._ensure_userid_column(conn)
            self._ensure_caseNotes_column(conn)
            self._ensure_endpoint_chain_column(conn)
        except Exception:
            logger.debug("Failed to ensure columns before fetch by uid")
        
        cursor = conn.execute("SELECT * FROM jobs WHERE uid = ?", (uid,))
        row = cursor.fetchone()
        
        if row:
            job_dict = self._row_to_dict(row)
            # Allow access only if job matches current user ID (explicit user string)
            try:
                from frontend.utils.nicegui_storage import get_user_id_for_jobs
                current_user_id = get_user_id_for_jobs()
            except Exception:
                current_user_id = None

            if current_user_id and job_dict.get('userId') and job_dict.get('userId') != current_user_id:
                logger.warning("Access denied for job %s: session mismatch", uid)
                return None
            try:
                job_record = JobRecord(**job_dict)
                return job_record
            except Exception as e:
                logger.error("Failed to validate job %s as JobRecord: %s", uid, e)
                # Return as dict for backward compatibility
                return None
        else:
            logger.debug("Job %s not found", uid)
            return None
    
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Get all jobs, sorted by start time (newest first).
        
        Returns:
            List[Dict[str, Any]]: List of job records as dictionaries
        
        Tips:
        - Jobs are sorted by startTime descending (newest first)
        - All jobs are validated as JobRecord models
        - Invalid jobs are skipped with warning logs
        - Job data is validated and then converted to a dictionary using extract_job_fields
        """
        conn = self.connect()
        # Ensure userId column exists for older DBs
        try:
            self._ensure_userid_column(conn)
            self._ensure_caseNotes_column(conn)
            self._ensure_endpoint_chain_column(conn)
        except Exception:
            logger.debug("Failed to ensure columns before fetching jobs; continuing without change")
        
        # Use a local import to avoid circular dependency issues
        # job_utils -> database -> job_db -> job_utils
        from frontend.pages.jobs.job_utils import extract_job_fields

        # Filter by explicit user ID only
        try:
            from frontend.utils.nicegui_storage import get_user_id_for_jobs
            current_user = get_user_id_for_jobs()
        except Exception:
            current_user = None

        if current_user:
            cursor = conn.execute("""
                SELECT * FROM jobs
                WHERE userId = ?
                ORDER BY startTime DESC
            """, (current_user,))
        else:
            cursor = conn.execute("SELECT * FROM jobs WHERE 1=0")
        
        jobs = []
        for row in cursor.fetchall():
            job_dict = self._row_to_dict(row)
            try:
                # Validate the data by creating a JobRecord instance
                job_record_validated = JobRecord(**job_dict)
                # Convert the validated object to a clean dictionary for the UI
                jobs.append(extract_job_fields(job_record_validated))
            except Exception as e:
                logger.warning("Failed to validate job %s as JobRecord: %s, skipping", job_dict.get('uid', 'unknown'), e)
        
        return jobs

    def get_job_count_for_user(self, user_id: Optional[str]) -> int:
        """
        Get count of jobs for a user (sync, lightweight).
        Returns 0 if user_id is None or on error.
        """
        if not user_id:
            return 0
        try:
            self._ensure_userid_column(self.connect())
            cursor = self.connect().execute(
                "SELECT COUNT(*) FROM jobs WHERE userId = ?", (user_id,)
            )
            return cursor.fetchone()[0] or 0
        except Exception as e:
            logger.debug("get_job_count_for_user failed: %s", e)
            return 0
    
    async def update_job_status(
        self,
        uid: str,
        status: JobStatus,
        response_body: Optional[Union[ResponseBody, Dict[str, Any]]] = None,
        status_text: Optional[str] = None,
        end_time: Optional[datetime] = None
    ) -> bool:
        """
        Update job status and optionally response.
        
        Args:
            uid (str): Job UID
            status (JobStatus): New status
            response_body (Optional[Union[ResponseBody, Dict[str, Any]]]): Response body.
                Can be ResponseBody Pydantic model or dict (for Completed status)
            status_text (Optional[str]): Status text (for Failed status)
            end_time (Optional[datetime]): End time (defaults to now if not provided)
        
        Returns:
            bool: True if job was updated, False if job not found
        
        Tips:
        - Sets end_time to current time if not provided
        - Stores response_body as JSON string in database
        - Accepts both ResponseBody Pydantic model and dict for backward compatibility
        """
        conn = self.connect()
        logger.info("Updating job %s status to %s", uid, status.value)
        
        if end_time is None:
            end_time = datetime.now()
        
        updates = {
            'status': status.value,
            'endTime': end_time.isoformat()
        }
        
        if response_body is not None:
            # Serialize response_body to JSON string
            if isinstance(response_body, ResponseBody):
                updates['response'] = json.dumps(response_body.model_dump(mode='json'))
            else:
                updates['response'] = json.dumps(response_body)
        
        if status_text is not None:
            updates['statusText'] = status_text
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [uid]
        
        cursor = conn.execute(f"UPDATE jobs SET {set_clause} WHERE uid = ?", values)
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info("Job %s updated successfully", uid)
            return True
        else:
            logger.warning("Job %s not found for update", uid)
            return False
    
    async def delete_job(self, uid: str) -> bool:
        """
        Delete job by UID.
        
        Args:
            uid (str): Job UID
        
        Returns:
            bool: True if job was deleted, False if job not found
        """
        conn = self.connect()
        logger.info("Deleting job %s", uid)
        
        cursor = conn.execute("DELETE FROM jobs WHERE uid = ?", (uid,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info("Job %s deleted successfully", uid)
            return True
        else:
            logger.warning("Job %s not found for deletion", uid)
            return False
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Convert SQLite Row to dictionary with JSON parsing.
        
        Parses JSON fields from database and returns dict ready for JobRecord validation.
        
        Args:
            row (sqlite3.Row): SQLite row object
        
        Returns:
            Dict[str, Any]: Dictionary with parsed JSON fields (ready for JobRecord)
        
        Tips:
        - Parses JSON strings to dicts for request, response, and taskSchema
        - Result can be passed directly to JobRecord(**job_dict) for validation
        """
        job = dict(row)
        
        # Parse JSON fields from database strings to dicts
        if job.get('request'):
            try:
                job['request'] = json.loads(job['request'])
            except json.JSONDecodeError as e:
                logger.error("Failed to parse request JSON: %s", e)
                job['request'] = {}
        
        if job.get('response'):
            try:
                job['response'] = json.loads(job['response'])
            except json.JSONDecodeError as e:
                logger.error("Failed to parse response JSON: %s", e)
                job['response'] = None
        
        if job.get('taskSchema'):
            try:
                job['taskSchema'] = json.loads(job['taskSchema'])
            except json.JSONDecodeError as e:
                logger.error("Failed to parse taskSchema JSON: %s", e)
                job['taskSchema'] = {}
        
        return job


# Global database instance
_job_db: Optional[JobDB] = None


async def init_database(db_path: Optional[Path] = None) -> JobDB:
    """
    Initialize database and return JobDB instance.
    
    Args:
        db_path (Optional[Path]): Path to database file
    
    Returns:
        JobDB: Initialized JobDB instance
    
    Tips:
    - Creates schema if it doesn't exist
    - Returns singleton instance for reuse
    """
    global _job_db
    
    if _job_db is None:
        _job_db = JobDB(db_path)
        await _job_db.initialize_schema()
    
    return _job_db


def get_job_db() -> JobDB:
    """
    Get global JobDB instance, initializing it if needed.
    
    Returns:
        JobDB: Global JobDB instance
    
    Tips:
    - Lazy initialization - database is created on first access
    - This avoids async initialization issues at module level
    - Schema is created automatically on first connection
    """
    global _job_db
    
    if _job_db is None:
        logger.info("Lazy-initializing job database")
        _job_db = JobDB()
        # Connect will auto-create schema if needed
        _job_db.connect()
    
    return _job_db

