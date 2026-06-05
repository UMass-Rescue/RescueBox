"""
Case Database Module

This module provides SQLite database functionality for storing and managing cases
in the RescueBox Desktop application.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid
from pydantic import BaseModel, Field

from frontend.database.base_db import BaseDatabase
from frontend.database.schemas import JobDatabaseSchema, SchemaManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CaseRecord(BaseModel):
    """Pydantic model for case records in the database."""
    caseId: str = Field(..., description="Unique case identifier")
    caseNumber: str = Field(..., description="Case number or ID")
    investigators: Optional[str] = Field(None, description="Names of investigators")
    evidencePath: str = Field(..., description="Path to evidence folder or UFDR file")
    createdAt: str = Field(..., description="ISO timestamp of creation")
    updatedAt: str = Field(..., description="ISO timestamp of last update")


class CaseDB(BaseDatabase):
    """
    Case database manager for SQLite storage.
    Manages case records in the SQLite database (jobs.db).
    """

    def __init__(self, db_path: Optional[Path] = None):
        super().__init__(db_path, "jobs.db")
        schema = JobDatabaseSchema()
        self.schema_manager = SchemaManager(schema)

    def _create_schema(self) -> None:
        """Create database schema for cases (part of JobDatabaseSchema)."""
        self.schema_manager.create_schema(self.conn)

    async def initialize_schema(self):
        """Initialize database schema (create cases table if it doesn't exist)."""
        conn = self.connect()
        logger.info("Initializing database schema for cases")
        self._create_schema()

    async def create_case(
        self,
        case_number: str,
        investigators: Optional[str],
        evidence_path: str,
    ) -> CaseRecord:
        """
        Create a new case record.
        """
        conn = self.connect()
        case_id = f"CASE_{uuid.uuid4().hex[:6]}"
        now = datetime.now().isoformat()

        case_record = CaseRecord(
            caseId=case_id,
            caseNumber=case_number.strip(),
            investigators=investigators.strip() if investigators else None,
            evidencePath=evidence_path.strip(),
            createdAt=now,
            updatedAt=now,
        )

        insert_sql = """
            INSERT INTO cases (caseId, caseNumber, investigators, evidencePath, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            case_record.caseId,
            case_record.caseNumber,
            case_record.investigators,
            case_record.evidencePath,
            case_record.createdAt,
            case_record.updatedAt,
        )

        try:
            conn.execute(insert_sql, params)
            conn.commit()
            logger.info("Case %s (%s) created successfully", case_id, case_number)
            return case_record
        except sqlite3.IntegrityError as e:
            logger.error("Failed to create case due to integrity error: %s", e)
            raise ValueError(f"Case number '{case_number}' already exists.")
        except Exception as e:
            logger.error("Failed to create case: %s", e)
            raise

    async def get_case_by_id(self, case_id: str) -> Optional[CaseRecord]:
        """Get a case by its ID."""
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM cases WHERE caseId = ?", (case_id,))
        row = cursor.fetchone()
        if row:
            return CaseRecord(**dict(row))
        return None

    def get_case_by_id_sync(self, case_id: str) -> Optional[CaseRecord]:
        """Get a case by its ID synchronously."""
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM cases WHERE caseId = ?", (case_id,))
        row = cursor.fetchone()
        if row:
            return CaseRecord(**dict(row))
        return None

    async def get_case_by_number(self, case_number: str) -> Optional[CaseRecord]:
        """Get a case by its case number."""
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM cases WHERE caseNumber = ?", (case_number.strip(),))
        row = cursor.fetchone()
        if row:
            return CaseRecord(**dict(row))
        return None

    async def get_all_cases(self) -> List[CaseRecord]:
        """Get all cases, sorted by creation time (newest first)."""
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM cases ORDER BY createdAt DESC")
        return [CaseRecord(**dict(row)) for row in cursor.fetchall()]

    def get_all_cases_sync(self) -> List[CaseRecord]:
        """Get all cases synchronously, sorted by creation time (newest first)."""
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM cases ORDER BY createdAt DESC")
        return [CaseRecord(**dict(row)) for row in cursor.fetchall()]

    async def update_case_evidence_path(self, case_id: str, new_path: str) -> bool:
        """Update the evidence path of a case."""
        conn = self.connect()
        now = datetime.now().isoformat()
        cursor = conn.execute(
            "UPDATE cases SET evidencePath = ?, updatedAt = ? WHERE caseId = ?",
            (new_path.strip(), now, case_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    async def delete_case(self, case_id: str) -> bool:
        """Delete a case by its ID."""
        conn = self.connect()
        cursor = conn.execute("DELETE FROM cases WHERE caseId = ?", (case_id,))
        conn.commit()
        return cursor.rowcount > 0


_case_db: Optional[CaseDB] = None


async def init_case_database(db_path: Optional[Path] = None) -> CaseDB:
    """Initialize case database and return CaseDB instance."""
    global _case_db
    if _case_db is None:
        _case_db = CaseDB(db_path)
        await _case_db.initialize_schema()
    return _case_db


def get_case_db() -> CaseDB:
    """Get global CaseDB instance, initializing it if needed."""
    global _case_db
    if _case_db is None:
        _case_db = CaseDB()
        _case_db.connect()
    return _case_db
