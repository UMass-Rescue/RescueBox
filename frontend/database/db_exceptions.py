"""Domain-specific exceptions for persistence layers and SQLite operations."""

from __future__ import annotations

import sqlite3


class DatabaseError(Exception):
    """Base exception for all database and persistence layer errors."""


class RecordNotFoundError(DatabaseError):
    """Raised when an expected record is not found in the database."""


class SchemaError(DatabaseError):
    """Raised when schema creation, migration, or validation fails."""


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection establishment fails."""


# Core tuple of exception types arising directly from database engine operations.
# Isolates SQLite errors and domain database errors without coupling to UI presentation exceptions.
DB_OPERATION_ERRORS = (sqlite3.Error, DatabaseError)

# Persistence catch tuple for query execution, row mapping, and JSON/field extraction,
# cleanly decoupled from UI_RENDER_ERRORS.
DB_ERRORS = (
    sqlite3.Error,
    DatabaseError,
    ValueError,
    TypeError,
    KeyError,
    AttributeError,
)

__all__ = [
    "DB_ERRORS",
    "DB_OPERATION_ERRORS",
    "DatabaseConnectionError",
    "DatabaseError",
    "RecordNotFoundError",
    "SchemaError",
]
