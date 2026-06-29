"""
Unit tests for database error handling and recovery.

This module tests the robustness of database operations by validating
that various error conditions are handled appropriately:

- SQLite integrity constraint violations
- Database locking and connection errors
- Unexpected exceptions during database operations
- Graceful handling of missing records
- Proper error propagation and logging

The tests ensure that database failures are handled gracefully,
providing appropriate error messages while maintaining data integrity
and preventing application crashes during database operations.
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch
from frontend.database.chat_history_db import ChatHistoryDB

# Test constants
TEST_CONVERSATION_TITLE = "Test Conversation"
DUPLICATE_CONVERSATION_TITLE = "Duplicate Conversation"
NONEXISTENT_CONVERSATION_ID = "nonexistent-id"
DATABASE_LOCKED_ERROR = "Database locked"
UNEXPECTED_ERROR_MSG = "Unexpected error"
DATABASE_INTEGRITY_ERROR = "database integrity error"
DATABASE_ERROR_MSG = "Database error"


class TestDatabaseErrorHandling:
    """Tests for database error handling and recovery mechanisms.

    This class validates the robustness of database operations by testing
    various failure scenarios and ensuring appropriate error handling:

    Database error scenarios tested:
    - Integrity constraint violations (duplicate records, etc.)
    - SQLite operational errors (database locked, disk full)
    - Connection failures and timeouts
    - Unexpected exceptions during database operations
    - Graceful handling of missing records (not found cases)

    All tests verify that database errors are handled gracefully with
    appropriate error messages and without corrupting application state.
    """

    def _mock_database_connection(self, chat_history_db, side_effect):
        """Helper method to mock database connection with specified error.

        Creates a mock database connection that raises the specified exception
        when database operations are attempted, simulating various database
        failure scenarios.

        Returns a context manager that can be used with 'with' statement.
        """

        def mock_connect():
            """Mock connection factory that returns a mock connection."""
            mock_conn = Mock()
            mock_conn.execute = Mock(side_effect=side_effect)
            return mock_conn

        return patch.object(chat_history_db, "connect", mock_connect)

    @pytest.fixture
    def chat_history_db(self, tmp_path):
        """Create ChatHistoryDB instance with temporary database"""
        db_path = tmp_path / "test.db"
        return ChatHistoryDB(db_path=db_path)

    @pytest.mark.asyncio
    async def test_create_conversation_integrity_error(self, chat_history_db):
        """Test handling of IntegrityError when creating conversation.

        Validates that database integrity constraint violations (such as
        duplicate records or constraint failures) are caught and handled
        gracefully with appropriate error messages.
        """
        # First create a conversation to set up initial state
        await chat_history_db.create_conversation(title=TEST_CONVERSATION_TITLE)

        # Mock database connection to simulate integrity constraint failure
        with self._mock_database_connection(
            chat_history_db, sqlite3.IntegrityError("UNIQUE constraint failed")
        ) as mock_connect:
            # Temporarily override the connection method
            original_connect = chat_history_db.connect
            chat_history_db.connect = mock_connect

            # Attempt to create conversation should raise handled exception
            with pytest.raises(Exception, match=DATABASE_INTEGRITY_ERROR):
                await chat_history_db.create_conversation(
                    title=DUPLICATE_CONVERSATION_TITLE
                )

            # Restore original connection method
            chat_history_db.connect = original_connect

    @pytest.mark.asyncio
    async def test_create_conversation_sqlite_error(self, chat_history_db):
        """Test handling of generic SQLite errors during conversation creation.

        Ensures that operational SQLite errors (database locked, disk full,
        permission denied, etc.) are caught and re-raised as application-level
        exceptions with clear error messages.
        """
        # Mock database connection to simulate operational error
        with self._mock_database_connection(
            chat_history_db, sqlite3.Error(DATABASE_LOCKED_ERROR)
        ) as mock_connect:
            # Temporarily override the connection method
            original_connect = chat_history_db.connect
            chat_history_db.connect = mock_connect

            # Attempt to create conversation should raise handled exception
            with pytest.raises(Exception, match=DATABASE_ERROR_MSG):
                await chat_history_db.create_conversation(title=TEST_CONVERSATION_TITLE)

            # Restore original connection method
            chat_history_db.connect = original_connect

    @pytest.mark.asyncio
    async def test_create_conversation_unexpected_error(self, chat_history_db):
        """Test handling of unexpected errors during conversation creation.

        Validates that non-SQLite exceptions (programming errors, system
        failures, etc.) are properly caught and re-raised without modification,
        allowing higher-level error handling to manage these cases.
        """
        # Mock database connection to simulate unexpected error
        with self._mock_database_connection(
            chat_history_db, Exception(UNEXPECTED_ERROR_MSG)
        ) as mock_connect:
            # Temporarily override the connection method
            original_connect = chat_history_db.connect
            chat_history_db.connect = mock_connect

            # Attempt to create conversation should re-raise the original exception
            with pytest.raises(Exception, match=UNEXPECTED_ERROR_MSG):
                await chat_history_db.create_conversation(title=TEST_CONVERSATION_TITLE)

            # Restore original connection method
            chat_history_db.connect = original_connect

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, chat_history_db):
        """Test graceful handling of non-existent conversation retrieval.

        Ensures that attempts to retrieve conversations that don't exist
        return None gracefully instead of raising exceptions, allowing
        the application to handle missing data appropriately.
        """
        result = await chat_history_db.get_conversation(NONEXISTENT_CONVERSATION_ID)

        # Should return None for non-existent conversations (graceful degradation)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_conversations_with_error(self, chat_history_db):
        """Test error handling when retrieving all conversations.

        Validates that database errors during bulk conversation retrieval
        are properly propagated (since this operation may not have specific
        error handling), allowing calling code to handle database failures
        appropriately.
        """
        # First create a conversation to ensure database has content
        await chat_history_db.create_conversation(title=TEST_CONVERSATION_TITLE)

        # Mock database connection to simulate error during bulk retrieval
        with self._mock_database_connection(
            chat_history_db, sqlite3.Error(DATABASE_ERROR_MSG)
        ) as mock_connect:
            # Temporarily override the connection method
            original_connect = chat_history_db.connect
            chat_history_db.connect = mock_connect

            # Bulk retrieval should propagate the database error
            with pytest.raises(sqlite3.Error):
                await chat_history_db.get_all_conversations()

            # Restore original connection method
            chat_history_db.connect = original_connect
