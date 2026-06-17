"""Pipeline-specific job queries and updates."""

from __future__ import annotations

import logging
import sqlite3
from typing import List, Optional

from frontend.database.job_db_migrations import (
    ensure_pipeline_columns,
    ensure_user_id_column,
)
from frontend.database.job_db_rows import row_to_job_dict
from frontend.database.db_exceptions import DB_ERRORS
from frontend.database.job_models import JobRecord

logger = logging.getLogger(__name__)


def list_jobs_for_pipeline_root(
    conn: sqlite3.Connection, user_id: str, root_uid: str
) -> List[JobRecord]:
    if not user_id or not root_uid:
        return []
    try:
        ensure_pipeline_columns(conn)
    except DB_ERRORS:
        logger.debug("pipeline column ensure failed before list_jobs_for_pipeline_root")
    cursor = conn.execute(
        """
        SELECT * FROM jobs
        WHERE userId = ? AND (pipelineRootJobId = ? OR uid = ?)
        ORDER BY startTime ASC
        """,
        (user_id, root_uid, root_uid),
    )
    out: List[JobRecord] = []
    for row in cursor.fetchall():
        job_dict = row_to_job_dict(row)
        try:
            out.append(JobRecord(**job_dict))
        except DB_ERRORS as e:
            logger.warning("Skip invalid job in pipeline list: %s", e)
    return out


def update_pipeline_metadata_filter_criteria(
    conn: sqlite3.Connection, uid: str, criteria: str
) -> bool:
    if not (uid or "").strip():
        return False
    try:
        ensure_pipeline_columns(conn)
    except DB_ERRORS:
        logger.debug("ensure pipelineMetadataFilterCriteria failed before update")
    capped = (criteria or "")[:4000]
    try:
        cur = conn.execute(
            "UPDATE jobs SET pipelineMetadataFilterCriteria = ? WHERE uid = ?",
            (capped, uid.strip()),
        )
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        logger.warning("update_pipeline_metadata_filter_criteria failed: %s", e)
        return False


def count_jobs_for_user(conn: sqlite3.Connection, user_id: Optional[str]) -> int:
    if not user_id:
        return 0
    try:
        ensure_user_id_column(conn)
        cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE userId = ?", (user_id,))
        return cursor.fetchone()[0] or 0
    except DB_ERRORS as e:
        logger.debug("count_jobs_for_user failed: %s", e)
        return 0
