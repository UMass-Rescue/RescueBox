"""
Database Schemas

This module defines database schema creation and management classes
for different database types used in the application.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DatabaseSchema(ABC):
    """Abstract base class for database schemas."""

    @abstractmethod
    def get_create_statements(self) -> list[str]:
        """
        Get SQL CREATE statements for this schema.

        Returns:
            List of SQL CREATE statements
        """
        raise NotImplementedError

    @abstractmethod
    def get_index_statements(self) -> list[str]:
        """
        Get SQL CREATE INDEX statements for this schema.

        Returns:
            List of SQL CREATE INDEX statements
        """
        raise NotImplementedError

    def get_all_statements(self) -> list[str]:
        """
        Get all SQL statements (tables and indexes).

        Returns:
            List of all SQL statements in correct order
        """
        return self.get_create_statements() + self.get_index_statements()


class JobDatabaseSchema(DatabaseSchema):
    """Schema for job database."""

    def get_create_statements(self) -> list[str]:
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
                userId TEXT,
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
            """
            CREATE TABLE IF NOT EXISTS cases (
                caseId TEXT PRIMARY KEY,
                caseNumber TEXT NOT NULL UNIQUE,
                investigators TEXT,
                evidencePath TEXT NOT NULL,
                createdAt TEXT NOT NULL,
                updatedAt TEXT NOT NULL
            )
            """,
        ]

    def get_index_statements(self) -> list[str]:
        """Get CREATE INDEX statements for job database."""
        return [
            "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_start_time ON jobs(startTime DESC)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_model_task ON jobs(modelUid, taskUid)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_endpoint ON jobs(endpoint)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_userId ON jobs(userId)",
            "CREATE INDEX IF NOT EXISTS filterID ON jobs(filterId)",
            "CREATE INDEX IF NOT EXISTS idx_file_filters_input_dir ON file_filters(input_dir)",
            "CREATE INDEX IF NOT EXISTS idx_file_filters_owner_id ON file_filters(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_cases_case_number ON cases(caseNumber)",
        ]


class ChatHistoryDatabaseSchema(DatabaseSchema):
    """Schema for chat history database."""

    def get_create_statements(self) -> list[str]:
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

    def get_index_statements(self) -> list[str]:
        """Get CREATE INDEX statements for chat history database."""
        return [
            "CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp ASC)",
            (
                "CREATE INDEX IF NOT EXISTS idx_messages_tool_calls "
                "ON messages(tool_call_endpoint) "
                "WHERE tool_call_endpoint IS NOT NULL"
            ),
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
            "tables": len(self.schema.get_create_statements()),
            "indexes": len(self.schema.get_index_statements()),
        }


def jobs_runtime_create_statements() -> list[str]:
    """
    Canonical CREATE statements used by ``JobDB.initialize_schema``.

    This is intentionally narrower than ``JobDatabaseSchema`` (jobs table only),
    because ``JobDB.initialize_schema`` should not own ``cases``/``file_filters``
    lifecycle. Those tables are created by their dedicated modules.
    """
    return [
        """
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
    """
    ]


def jobs_runtime_index_statements() -> list[str]:
    """Canonical index statements paired with :func:`jobs_runtime_create_statements`."""
    return [
        "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_modelUid ON jobs(modelUid)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_userId ON jobs(userId)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_startTime ON jobs(startTime)",
        "CREATE INDEX IF NOT EXISTS filterID ON jobs(filterId)",
    ]


def chat_history_runtime_create_statements() -> list[str]:
    """
    Canonical CREATE statements used by ``ChatHistoryDB._create_schema``.

    Keep these aligned with the runtime table names used by the chat module:
    ``conversations`` and ``chat_messages``.
    """
    return [
        """
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            userId TEXT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            message_count INTEGER DEFAULT 0,
            metadata TEXT
        )
    """,
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            tool_calls TEXT,
            tool_call_endpoint TEXT,
            tool_call_arguments TEXT,
            timestamp TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
        )
    """,
    ]


def chat_history_runtime_index_statements() -> list[str]:
    """Canonical index statements paired with :func:`chat_history_runtime_create_statements`."""
    return [
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id ON chat_messages(conversation_id)",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_tool_call_endpoint ON chat_messages(tool_call_endpoint)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at)",
    ]


def cases_runtime_create_statements() -> list[str]:
    """Canonical CREATE statements used by ``CaseDB._create_schema``."""
    return [
        """
        CREATE TABLE IF NOT EXISTS cases (
            caseId TEXT PRIMARY KEY,
            caseNumber TEXT NOT NULL UNIQUE,
            investigators TEXT,
            evidencePath TEXT NOT NULL,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        )
    """
    ]


def cases_runtime_index_statements() -> list[str]:
    """Canonical index statements paired with :func:`cases_runtime_create_statements`."""
    return [
        "CREATE INDEX IF NOT EXISTS idx_cases_case_number ON cases(caseNumber)",
    ]


def file_filters_runtime_create_statements() -> list[str]:
    """Canonical CREATE statements used by ``file_filter_store`` helpers."""
    return [
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
    """
    ]


def file_filters_runtime_index_statements() -> list[str]:
    """Canonical index statements paired with :func:`file_filters_runtime_create_statements`."""
    return [
        "CREATE INDEX IF NOT EXISTS idx_file_filters_input_dir ON file_filters(input_dir)",
        "CREATE INDEX IF NOT EXISTS idx_file_filters_owner_id ON file_filters(owner_id)",
    ]
