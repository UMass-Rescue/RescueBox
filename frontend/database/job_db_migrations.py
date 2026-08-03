"""Runtime SQLite migrations for the ``jobs`` table (additive columns)."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable

logger = logging.getLogger(__name__)


def _add_column_if_missing(
    conn: sqlite3.Connection,
    *,
    column: str,
    alter_sql: str,
    index_sql: str | None = None,
) -> None:
    try:
        conn.execute(f"SELECT {column} FROM jobs LIMIT 1")
    except sqlite3.OperationalError as e:
        if "no such column" not in str(e).lower():
            raise
        logger.debug("%s column missing in jobs table; adding column", column)
        try:
            conn.execute(alter_sql)
            if index_sql:
                conn.execute(index_sql)
            conn.commit()
            logger.debug("Added %s column to jobs table", column)
        except Exception as e_add:
            logger.exception("Failed to add %s column to jobs table: %s", column, e_add)
            raise


def ensure_user_id_column(conn: sqlite3.Connection) -> None:
    """Ensure ``userId`` exists (older DBs)."""
    _add_column_if_missing(
        conn,
        column="userId",
        alter_sql="ALTER TABLE jobs ADD COLUMN userId TEXT",
        index_sql="CREATE INDEX IF NOT EXISTS idx_jobs_userId ON jobs(userId)",
    )


def ensure_case_notes_column(conn: sqlite3.Connection) -> None:
    """Ensure ``caseNotes`` exists."""
    _add_column_if_missing(
        conn,
        column="caseNotes",
        alter_sql="ALTER TABLE jobs ADD COLUMN caseNotes TEXT",
    )


def ensure_endpoint_chain_column(conn: sqlite3.Connection) -> None:
    """Ensure ``endpointChain`` exists (multi-step chatbot jobs)."""
    _add_column_if_missing(
        conn,
        column="endpointChain",
        alter_sql="ALTER TABLE jobs ADD COLUMN endpointChain TEXT",
    )


def ensure_pipeline_root_job_id_column(conn: sqlite3.Connection) -> None:
    """Ensure ``pipelineRootJobId`` exists."""
    _add_column_if_missing(
        conn,
        column="pipelineRootJobId",
        alter_sql="ALTER TABLE jobs ADD COLUMN pipelineRootJobId TEXT",
        index_sql=(
            "CREATE INDEX IF NOT EXISTS idx_jobs_pipelineRootJobId "
            "ON jobs(pipelineRootJobId)"
        ),
    )


def ensure_pipeline_metadata_filter_criteria_column(conn: sqlite3.Connection) -> None:
    """Ensure ``pipelineMetadataFilterCriteria`` exists."""
    _add_column_if_missing(
        conn,
        column="pipelineMetadataFilterCriteria",
        alter_sql=("ALTER TABLE jobs ADD COLUMN pipelineMetadataFilterCriteria TEXT"),
    )


_ALL_COLUMN_ENSURES: tuple[Callable[[sqlite3.Connection], None], ...] = (
    ensure_user_id_column,
    ensure_case_notes_column,
    ensure_endpoint_chain_column,
    ensure_pipeline_root_job_id_column,
    ensure_pipeline_metadata_filter_criteria_column,
)


def ensure_all_job_columns(conn: sqlite3.Connection) -> None:
    """Apply all additive column migrations on ``jobs``."""
    for ensure in _ALL_COLUMN_ENSURES:
        ensure(conn)


def ensure_pipeline_columns(conn: sqlite3.Connection) -> None:
    """Migrations needed for pipeline listing / metadata filter only."""
    ensure_pipeline_root_job_id_column(conn)
    ensure_pipeline_metadata_filter_criteria_column(conn)
