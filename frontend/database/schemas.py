"""
Database Schemas

This module defines database schema creation and management classes
for different database types used in the application.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)


class DatabaseSchema(ABC):
    """Abstract base class for database schemas."""

    @abstractmethod
    def get_create_statements(self) -> List[str]:
        """
        Get SQL CREATE statements for this schema.

        Returns:
            List of SQL CREATE statements
        """
        pass

    @abstractmethod
    def get_index_statements(self) -> List[str]:
        """
        Get SQL CREATE INDEX statements for this schema.

        Returns:
            List of SQL CREATE INDEX statements
        """
        pass

    def get_all_statements(self) -> List[str]:
        """
        Get all SQL statements (tables and indexes).

        Returns:
            List of all SQL statements in correct order
        """
        return self.get_create_statements() + self.get_index_statements()


class JobDatabaseSchema(DatabaseSchema):
    """Schema for job database."""

    def get_create_statements(self) -> List[str]:
        """Get CREATE TABLE statements for job database."""
        return [
            """
            CREATE TABLE IF NOT EXISTS jobs (
                uid TEXT PRIMARY KEY,
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
            """,
            """
            CREATE TABLE IF NOT EXISTS file_filters (
                id TEXT PRIMARY KEY,
                name TEXT,
                input_dir TEXT,
                filter_type TEXT NOT NULL DEFAULT 'input',
                paths_json TEXT,
                patterns_json TEXT,
                owner_id TEXT,
                source TEXT,
                metadata TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
        ]

    def get_index_statements(self) -> List[str]:
        """Get CREATE INDEX statements for job database."""
        return [
            "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_start_time ON jobs(startTime DESC)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_model_task ON jobs(modelUid, taskUid)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_endpoint ON jobs(endpoint)",
            "CREATE INDEX IF NOT EXISTS filterID ON jobs(filterId)",
            "CREATE INDEX IF NOT EXISTS idx_file_filters_input_dir ON file_filters(input_dir)",
            "CREATE INDEX IF NOT EXISTS idx_file_filters_owner_id ON file_filters(owner_id)",
        ]


class ChatHistoryDatabaseSchema(DatabaseSchema):
    """Schema for chat history database."""

    def get_create_statements(self) -> List[str]:
        """Get CREATE TABLE statements for chat history database."""
        return [
            """
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message_count INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                message_type TEXT DEFAULT 'text',
                tool_calls TEXT,
                tool_call_endpoint TEXT,
                tool_call_arguments TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id) ON DELETE CASCADE
            )
            """,
        ]

    def get_index_statements(self) -> List[str]:
        """Get CREATE INDEX statements for chat history database."""
        return [
            "CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp ASC)",
            "CREATE INDEX IF NOT EXISTS idx_messages_tool_calls ON messages(tool_call_endpoint) WHERE tool_call_endpoint IS NOT NULL",
        ]


class SchemaManager:
    """Manages database schema creation and updates."""

    def __init__(self, schema: DatabaseSchema):
        """
        Initialize schema manager.

        Args:
            schema: Database schema to manage
        """
        self.schema = schema

    def create_schema(self, connection) -> None:
        """
        Create database schema using the provided connection.

        Args:
            connection: SQLite database connection
        """
        logger.info("Creating database schema")

        # Execute all schema statements
        for statement in self.schema.get_all_statements():
            connection.execute(statement.strip())

        logger.info("Database schema created successfully")

    def get_schema_info(self) -> dict:
        """
        Get information about the schema.

        Returns:
            Dict with schema information
        """
        return {
            'tables': len(self.schema.get_create_statements()),
            'indexes': len(self.schema.get_index_statements()),
        }
