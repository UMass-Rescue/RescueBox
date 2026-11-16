"""
Base Database Class

This module provides a base class for SQLite database operations,
extracting common functionality used by different database modules.
"""

import logging
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from frontend.config import DATA_DIR

logger = logging.getLogger(__name__)


class BaseDatabase(ABC):
    """
    Base class for SQLite database operations.

    Provides common functionality for database initialization, connection management,
    schema creation, and basic CRUD operations.
    """

    def __init__(self, db_path: Path | None = None, db_filename: str = "database.db"):
        """
        Initialize database with path configuration.

        Args:
            db_path: Optional custom database path
            db_filename: Default filename for database file
        """
        if db_path is None:
            # Use data directory in frontend folder
            data_dir = DATA_DIR
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / db_filename

        self.db_path = db_path
        self.conn: sqlite3.Connection | None = None
        self._initialized = False

        logger.info(
            "%s initialized with database path: %s",
            self.__class__.__name__,
            db_path,
        )

    def connect(self) -> sqlite3.Connection:
        """
        Connect to SQLite database with standard configuration.

        Returns:
            sqlite3.Connection: Database connection
        """
        if self.conn is None:
            logger.debug("Connecting to database: %s", self.db_path)
            # Use a longer timeout and allow multi-threaded access where appropriate.
            # Enable WAL journal mode and a busy timeout to reduce "database is locked" errors.
            self.conn = sqlite3.connect(
                str(self.db_path), timeout=30, check_same_thread=False
            )
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL for better concurrency
            try:
                self.conn.execute("PRAGMA journal_mode = WAL")
            except sqlite3.Error:
                # Older SQLite may ignore WAL; proceed silently
                pass
            # Set busy timeout (milliseconds)
            try:
                self.conn.execute("PRAGMA busy_timeout = 5000")
            except sqlite3.Error:
                pass

            # Initialize schema if not already done
            if not self._initialized:
                self._create_schema()
                self._initialized = True

            logger.info("Database connection established")

        return self.conn

    def close_connection(self) -> None:
        """Close database connection with logging."""
        if self.conn:
            logger.debug("Closing database connection")
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    def close(self) -> None:
        """Close database connection."""
        self.close_connection()

    @abstractmethod
    def _create_schema(self) -> None:
        """
        Create database schema.

        Must be implemented by subclasses to define their specific tables
        and indexes.
        """
        raise NotImplementedError

    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query with error handling.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            sqlite3.Cursor: Query cursor
        """
        conn = self.connect()
        try:
            return conn.execute(query, params)
        except sqlite3.Error:
            logger.error("Database query failed: %s with params %s", query, params)
            raise

    def commit(self) -> None:
        """Commit current transaction."""
        if self.conn:
            self.conn.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        if self.conn:
            self.conn.rollback()

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """
        Convert SQLite Row to dictionary.

        Args:
            row: SQLite Row object

        Returns:
            Dict containing row data
        """
        return dict(row)

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        cursor = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return cursor.fetchone() is not None
