"""Unit tests for domain-specific persistence exceptions."""

import sqlite3
import subprocess

from frontend.database.db_exceptions import (
    DB_ERRORS,
    DB_OPERATION_ERRORS,
    DatabaseConnectionError,
    DatabaseError,
    RecordNotFoundError,
    SchemaError,
)


def test_database_error_hierarchy():
    """Verify clean inheritance of persistence domain exceptions."""
    assert issubclass(RecordNotFoundError, DatabaseError)
    assert issubclass(SchemaError, DatabaseError)
    assert issubclass(DatabaseConnectionError, DatabaseError)
    assert issubclass(DatabaseError, Exception)


def test_db_operation_errors_composition():
    """Verify DB_OPERATION_ERRORS contains SQLite and domain database errors."""
    assert sqlite3.Error in DB_OPERATION_ERRORS
    assert DatabaseError in DB_OPERATION_ERRORS


def test_db_errors_decoupled_from_ui_exceptions():
    """Verify UI render exceptions are NOT coupled into database error tuples."""
    assert subprocess.CalledProcessError not in DB_ERRORS
    assert AssertionError not in DB_ERRORS
    assert OSError not in DB_ERRORS


def test_record_not_found_instantiation():
    """Verify RecordNotFoundError can be instantiated and raised cleanly."""
    err = RecordNotFoundError("Job with uid JOB_123 not found")
    assert str(err) == "Job with uid JOB_123 not found"
    assert isinstance(err, DatabaseError)
