"""Read paths for jobs (user scope, listing, single-row load)."""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Dict, List, Optional

from frontend.database.db_exceptions import DB_ERRORS
from frontend.database.job_field_utils import extract_job_fields
from frontend.database.job_models import JobRecord
from frontend.database.job_db_rows import row_to_job_dict
from frontend.utils.storage import get_user_id_for_jobs

logger = logging.getLogger(__name__)


def current_user_id_for_jobs() -> Optional[str]:
    try:
        return get_user_id_for_jobs()
    except DB_ERRORS:
        return None


def job_dict_allowed_for_user(
    job_dict: Dict[str, Any], current_user_id: Optional[str]
) -> bool:
    if not current_user_id:
        return True
    owner = job_dict.get("userId")
    if owner and owner != current_user_id:
        return False
    return True


def load_job_record_from_row(
    row: sqlite3.Row,
    *,
    uid: str,
    enforce_user_scope: bool = True,
) -> Optional[JobRecord]:
    job_dict = row_to_job_dict(row)
    if enforce_user_scope:
        current_user_id = current_user_id_for_jobs()
        if not job_dict_allowed_for_user(job_dict, current_user_id):
            logger.warning("Access denied for job %s: session mismatch", uid)
            return None
    try:
        return JobRecord(**job_dict)
    except DB_ERRORS as e:
        logger.error("Failed to validate job %s as JobRecord: %s", uid, e)
        return None


def fetch_job_by_uid(
    conn: sqlite3.Connection, uid: str, *, enforce_user_scope: bool = True
) -> Optional[JobRecord]:
    cursor = conn.execute("SELECT * FROM jobs WHERE uid = ?", (uid,))
    row = cursor.fetchone()
    if not row:
        logger.debug("Job %s not found", uid)
        return None
    return load_job_record_from_row(row, uid=uid, enforce_user_scope=enforce_user_scope)


def fetch_all_jobs_for_current_user(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    current_user = current_user_id_for_jobs()
    if current_user:
        cursor = conn.execute(
            """
            SELECT * FROM jobs
            WHERE userId = ?
            ORDER BY startTime DESC
            """,
            (current_user,),
        )
    else:
        cursor = conn.execute("SELECT * FROM jobs WHERE 1=0")

    jobs: List[Dict[str, Any]] = []
    for row in cursor.fetchall():
        job_dict = row_to_job_dict(row)
        try:
            job_record_validated = JobRecord(**job_dict)
            jobs.append(extract_job_fields(job_record_validated))
        except DB_ERRORS as e:
            logger.warning(
                "Failed to validate job %s as JobRecord: %s, skipping",
                job_dict.get("uid", "unknown"),
                e,
            )
    return jobs
