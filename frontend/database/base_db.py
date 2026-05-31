"""
Base Database Class

This module provides a base class for SQLite database operations,
extracting common functionality used by different database modules.
"""

import logging
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

from frontend.config import DATA_DIR

logger = logging.getLogger(__name__)


class BaseDatabase(ABC):
    """
    Base class for SQLite database operations.

    Provides common functionality for database initialization, connection management,
    schema creation, and basic CRUD operations.
    """

    def __init__(self, db_path: Optional[Path] = None, db_filename: str = "database.db"):
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
        self.conn: Optional[sqlite3.Connection] = None
        self._initialized = False

        logger.info(f"{self.__class__.__name__} initialized with database path: {db_path}")

    def connect(self) -> sqlite3.Connection:
        """
        Connect to SQLite database with standard configuration.

        Returns:
            sqlite3.Connection: Database connection
        """
        if self.conn is None:
            logger.debug(f"Connecting to database: {self.db_path}")
            # Use a longer timeout and allow multi-threaded access where appropriate.
            # Enable WAL journal mode and a busy timeout to reduce "database is locked" errors.
            self.conn = sqlite3.connect(str(self.db_path), timeout=30, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            # Enable foreign keys
            self.conn.execute('PRAGMA foreign_keys = ON')
            # Enable WAL for better concurrency
            try:
                self.conn.execute('PRAGMA journal_mode = WAL')
            except sqlite3.Error:
                # Older SQLite may ignore WAL; proceed silently
                pass
            # Set busy timeout (milliseconds)
            try:
                self.conn.execute('PRAGMA busy_timeout = 5000')
            except sqlite3.Error:
                pass

            # Initialize schema if not already done
            if not self._initialized:
                self._create_schema()
                self._initialized = True

            logger.info("Database connection established")

        return self.conn

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    @abstractmethod
    def _create_schema(self) -> None:
        """
        Create database schema.

        Must be implemented by subclasses to define their specific tables
        and indexes.
        """
        pass

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
            logger.error(f"Database query failed: {query} with params {params}")
            raise

    def execute_query_many(self, query: str, params_list: list) -> sqlite3.Cursor:
        """
        Execute a SQL query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            sqlite3.Cursor: Query cursor
        """
        conn = self.connect()
        try:
            return conn.executemany(query, params_list)
        except sqlite3.Error:
            logger.error(f"Database query failed: {query} with params {params_list}")
            raise

    def commit(self) -> None:
        """Commit current transaction."""
        if self.conn:
            self.conn.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        if self.conn:
            self.conn.rollback()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Convert SQLite Row to dictionary.

        Args:
            row: SQLite Row object

        Returns:
            Dict containing row data
        """
        return dict(row)

    def get_row_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows in the table
        """
        cursor = self.execute_query(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]

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
            (table_name,)
        )
        return cursor.fetchone() is not None

    def get_table_schema(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dict with table schema information or None if table doesn't exist
        """
        cursor = self.execute_query("PRAGMA table_info(?)", (table_name,))
        columns = cursor.fetchall()

        if not columns:
            return None

        return {
            'table_name': table_name,
            'columns': [self._row_to_dict(col) for col in columns]
        }
