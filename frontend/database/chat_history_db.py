"""
Chat History Database Module

This module provides SQLite database functionality for storing and managing
chat conversation history, including user prompts, assistant responses, and
tool calls. It enables users to recall previous conversations and re-run
tool calls from history.

Usage:
    from frontend.database import get_chat_history_db
    
    chat_history = get_chat_history_db()
    
    # Create conversation
    conversation = await chat_history.create_conversation()
    
    # Add messages
    await chat_history.add_message(
        conversation_id=conversation.conversation_id,
        role='user',
        content="Find faces in images"
    )
    
    # Get conversation history
    messages = await chat_history.get_messages(conversation.conversation_id)
"""

import logging
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

# Import refactored components
from .base_db import BaseDatabase
from .schemas import ChatHistoryDatabaseSchema, SchemaManager
from .validation import DatabaseValidator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ConversationRecord(BaseModel):
    """
    Pydantic model for conversation records.
    
    Represents a conversation with metadata including title, timestamps,
    and message count.
    """
    conversation_id: str = Field(..., description="Unique conversation identifier")
    title: str = Field(..., description="Conversation title")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")
    message_count: int = Field(default=0, description="Number of messages in conversation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata as JSON")


class ChatMessageRecord(BaseModel):
    """
    Pydantic model for chat message records.
    
    Represents a single message in a conversation, including user prompts,
    assistant responses, and tool calls.
    """
    message_id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Conversation ID this message belongs to")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")
    message_type: str = Field(default='text', description="Message type: 'text', 'tool_call', 'tool_result', 'error'")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls as list of dicts")
    tool_call_endpoint: Optional[str] = Field(None, description="Endpoint name from tool call")
    tool_call_arguments: Optional[Dict[str, Any]] = Field(None, description="Tool call arguments")
    timestamp: str = Field(..., description="Message timestamp (ISO format)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata as JSON")


class ChatHistoryDB(BaseDatabase):
    """
    Chat history database manager for SQLite storage.
    
    Manages conversation and message records in SQLite database, providing
    functionality to store, retrieve, and manage chat history.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize ChatHistoryDB.

        Args:
            db_path: Optional path to database file. Defaults to frontend/data/jobs.db
        """
        super().__init__(db_path, "jobs.db")  # Same database as jobs

        # Initialize schema manager
        schema = ChatHistoryDatabaseSchema()
        self.schema_manager = SchemaManager(schema)

        # Initialize validator
        self.validator = DatabaseValidator()
    
    def connect(self) -> sqlite3.Connection:
        """
        Connect to SQLite database and ensure schema exists.

        Returns:
            sqlite3.Connection: Database connection

        Note:
            Schema initialization is handled by the base class
        """
        return super().connect()

    def _create_schema(self) -> None:
        """
        Create database schema for chat history.

        This method is called by the base class during connection.
        """
        self.schema_manager.create_schema(self.conn)
    
    def _create_schema(self):
        """
        Create database schema for conversations and messages.
        
        Creates tables if they don't exist and adds indexes for performance.
        """
        logger.debug("Creating chat history schema")
        
        # Conversations table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                userId TEXT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        
        # Chat messages table
        self.conn.execute("""
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
        """)
        
        # Indexes for performance
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id ON chat_messages(conversation_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_tool_call_endpoint ON chat_messages(tool_call_endpoint)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at)")
        
        self.conn.commit()
        logger.debug("Chat history schema created/verified")

    def _ensure_conversations_userid_column(self, conn: sqlite3.Connection) -> None:
        """
        Ensure `userId` column exists on conversations table. Adds it if missing.
        """
        try:
            conn.execute("SELECT userId FROM conversations LIMIT 1")
        except sqlite3.OperationalError as e:
            if 'no such column' in str(e).lower():
                logger.debug("userId column missing in conversations table; adding column")
                try:
                    conn.execute("ALTER TABLE conversations ADD COLUMN userId TEXT")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_userId ON conversations(userId)")
                    conn.commit()
                    logger.debug("Added userId column and index to conversations table")
                except Exception as e_add:
                    logger.exception("Failed to add userId column to conversations table: %s", e_add)
                    raise
            else:
                raise

    def _get_current_user(self) -> Optional[str]:
        """Return current NiceGUI session/user id or None."""
        try:
            from frontend.utils.nicegui_storage import get_user_id_for_jobs
            return get_user_id_for_jobs()
        except Exception:
            return None

    def _conversation_user_id(self, conn: sqlite3.Connection, conversation_id: str) -> Optional[str]:
        """Return the userId for a conversation or None if not set/found."""
        try:
            cursor = conn.execute("SELECT userId FROM conversations WHERE conversation_id = ?", (conversation_id,))
            row = cursor.fetchone()
            if row:
                return row.get("userId")
        except Exception as e:
            logger.debug("Failed to fetch conversation userId: %s", e)
        return None
    
    def close(self):
        """Close database connection."""
        if self.conn:
            logger.debug("Closing database connection")
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")
    
    async def create_conversation(self, title: Optional[str] = None) -> ConversationRecord:
        """
        Create a new conversation.
        
        Args:
            title: Optional conversation title. If not provided, will be auto-generated
                   from first message or use default.
        
        Returns:
            ConversationRecord: Created conversation record
        """
        conversation_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        title = title or f"Conversation {now[:10]}"
        
        try:
            conn = self.connect()
            # Ensure userId column exists for older DBs
            try:
                self._ensure_conversations_userid_column(conn)
            except Exception:
                logger.debug("Failed to ensure conversations.userId column before insert")

            # Determine current session/user id if available
            try:
                from frontend.utils.nicegui_storage import get_user_id_for_jobs
                user_id = get_user_id_for_jobs()
            except Exception:
                user_id = None

            logger.debug("Creating conversation: %s (user=%s)", conversation_id, user_id)
            
            conn.execute("""
                INSERT INTO conversations (conversation_id, userId, title, created_at, updated_at, message_count)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (conversation_id, user_id, title, now, now))
            
            conn.commit()
            logger.debug("Conversation %s created", conversation_id)
            
            return ConversationRecord(
                conversation_id=conversation_id,
                title=title,
                created_at=now,
                updated_at=now,
                message_count=0,
                metadata={"userId": user_id} if user_id else None
            )
        except sqlite3.IntegrityError as e:
            logger.error("Database integrity error creating conversation: %s", str(e))
            raise Exception(f"Failed to create conversation: database integrity error") from e
        except sqlite3.Error as e:
            logger.error("Database error creating conversation: %s", str(e))
            raise Exception(f"Database error creating conversation: {str(e)}") from e
        except Exception as e:
            logger.error("Unexpected error creating conversation: %s", str(e))
            raise Exception(f"Unexpected error creating conversation: {str(e)}") from e
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationRecord]:
        """
        Get conversation by ID.
        
        Args:
            conversation_id: Conversation unique identifier
        
        Returns:
            Optional[ConversationRecord]: Conversation record if found, None otherwise
        """
        conn = self.connect()
        try:
            self._ensure_conversations_userid_column(conn)
        except Exception:
            logger.debug("Failed to ensure conversations.userId column before fetch by id")
        logger.debug("Fetching conversation: %s", conversation_id)
        
        cursor = conn.execute(
            "SELECT * FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return ConversationRecord(**self._row_to_dict(row))
        return None
    
    async def get_all_conversations(self) -> List[ConversationRecord]:
        """
        Get all conversations, sorted by updated_at (newest first).
        
        Returns:
            List[ConversationRecord]: List of conversation records
        """
        conn = self.connect()
        logger.debug("Fetching all conversations from database")

        # Ensure column exists and filter by current NiceGUI session/user if available
        try:
            self._ensure_conversations_userid_column(conn)
        except Exception:
            logger.debug("Failed to ensure conversations.userId column before fetching conversations")

        try:
            from frontend.utils.nicegui_storage import get_user_id_for_jobs
            current_user = get_user_id_for_jobs()
        except Exception:
            current_user = None

        if current_user:
            cursor = conn.execute("""
                SELECT * FROM conversations
                WHERE userId = ?
                ORDER BY updated_at DESC
            """, (current_user,))
        else:
            cursor = conn.execute("""
                SELECT * FROM conversations
                ORDER BY updated_at DESC
            """)

        rows = cursor.fetchall()
        logger.debug("SQL query returned %d rows", len(rows))

        conversations = []
        for row in rows:
            logger.debug("Processing conversation row: %s", dict(row))
            conv_dict = self._row_to_dict(row)
            logger.debug("Converted to dict: %s", conv_dict)
            conv_record = ConversationRecord(**conv_dict)
            conversations.append(conv_record)
            logger.debug("Created ConversationRecord: %s", conv_record.conversation_id)

        logger.debug("Fetched %d conversations total", len(conversations))
        return conversations

    async def get_message(self, message_id: str) -> Optional[ChatMessageRecord]:
        """
        Get message by ID with ownership check (if current session available).
        """
        conn = self.connect()
        logger.debug("Fetching message: %s", message_id)

        cursor = conn.execute(
            "SELECT * FROM chat_messages WHERE message_id = ?",
            (message_id,)
        )
        row = cursor.fetchone()

        if not row:
            return None

        # Ownership check: if current_user exists, ensure message's conversation belongs to them
        current_user = self._get_current_user()
        if current_user:
            conv_user = self._conversation_user_id(conn, row["conversation_id"])
            if conv_user and conv_user != current_user:
                logger.warning("Access denied to message %s for user %s", message_id, current_user)
                return None

        return self._message_row_to_record(row)
    
    async def update_conversation(self, conversation_id: str, **updates) -> bool:
        """
        Update conversation metadata.
        
        Args:
            conversation_id: Conversation unique identifier
            **updates: Fields to update (title, metadata, etc.)
        
        Returns:
            bool: True if update successful, False otherwise
        """
        conn = self.connect()
        logger.info("Updating conversation: %s", conversation_id)
        
        # Update updated_at timestamp
        updates['updated_at'] = datetime.now().isoformat()
        
        # Build update query
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [conversation_id]
        
        cursor = conn.execute(
            f"UPDATE conversations SET {set_clause} WHERE conversation_id = ?",
            values
        )
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info("Conversation %s updated", conversation_id)
            return True
        return False
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete conversation and all its messages.
        
        Args:
            conversation_id: Conversation unique identifier
        
        Returns:
            bool: True if deletion successful, False otherwise
        """
        conn = self.connect()
        logger.info("Deleting conversation: %s", conversation_id)
        
        cursor = conn.execute(
            "DELETE FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        )
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info("Conversation %s deleted", conversation_id)
            return True
        return False
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_type: str = 'text',
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_endpoint: Optional[str] = None,
        tool_call_arguments: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessageRecord:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation unique identifier
            role: Message role ('user' or 'assistant')
            content: Message text content
            message_type: Message type ('text', 'tool_call', 'tool_result', 'error')
            tool_calls: List of tool call dictionaries (for assistant messages)
            tool_call_endpoint: Endpoint name from tool call (for easy filtering)
            tool_call_arguments: Tool call arguments dictionary
            metadata: Additional metadata dictionary
        
        Returns:
            ChatMessageRecord: Created message record
        """
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        conn = self.connect()
        logger.debug("Adding message to conversation: %s", conversation_id)

        # Ownership check: ensure current user owns the conversation when session present
        current_user = self._get_current_user()
        if current_user:
            conv_user = self._conversation_user_id(conn, conversation_id)
            if conv_user and conv_user != current_user:
                logger.warning("Access denied to add message to conversation %s for user %s", conversation_id, current_user)
                raise Exception("Access denied to conversation")
        
        # Serialize JSON fields
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        tool_call_arguments_json = json.dumps(tool_call_arguments) if tool_call_arguments else None
        metadata_json = json.dumps(metadata) if metadata else None
        
        conn.execute("""
            INSERT INTO chat_messages (
                message_id, conversation_id, role, content, message_type,
                tool_calls, tool_call_endpoint, tool_call_arguments,
                timestamp, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id, conversation_id, role, content, message_type,
            tool_calls_json, tool_call_endpoint, tool_call_arguments_json,
            timestamp, metadata_json
        ))
        
        # Update conversation message count and updated_at
        conn.execute("""
            UPDATE conversations
            SET message_count = message_count + 1,
                updated_at = ?
            WHERE conversation_id = ?
        """, (timestamp, conversation_id))
        
        # Auto-generate title from first user message if not set
        if role == 'user' and content:
            conv = await self.get_conversation(conversation_id)
            if conv and conv.title.startswith('Conversation'):
                # Generate title from first 50 chars of message
                title = content[:50] + ('...' if len(content) > 50 else '')
                await self.update_conversation(conversation_id, title=title)
        
        conn.commit()
        logger.debug("Message %s added to conversation %s", message_id, conversation_id)
        
        return ChatMessageRecord(
            message_id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_type=message_type,
            tool_calls=tool_calls,
            tool_call_endpoint=tool_call_endpoint,
            tool_call_arguments=tool_call_arguments,
            timestamp=timestamp,
            metadata=metadata
        )
    
    async def get_messages(self, conversation_id: str) -> List[ChatMessageRecord]:
        """
        Get all messages for a conversation, sorted by timestamp.
        
        Args:
            conversation_id: Conversation unique identifier
        
        Returns:
            List[ChatMessageRecord]: List of message records
        """
        conn = self.connect()
        logger.debug("Fetching messages for conversation: %s", conversation_id)

        # Ownership check: ensure current user owns the conversation when session present
        current_user = self._get_current_user()
        if current_user:
            conv_user = self._conversation_user_id(conn, conversation_id)
            if conv_user and conv_user != current_user:
                logger.warning("Access denied to fetch messages for conversation %s for user %s", conversation_id, current_user)
                return []

        cursor = conn.execute("""
            SELECT * FROM chat_messages
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        """, (conversation_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append(self._message_row_to_record(row))
        
        logger.debug("Fetched %d messages for conversation %s", len(messages), conversation_id)
        return messages
    
    # get_message is implemented above with ownership checks
    
    async def delete_message(self, message_id: str) -> bool:
        """
        Delete a message.
        
        Args:
            message_id: Message unique identifier
        
        Returns:
            bool: True if deletion successful, False otherwise
        """
        conn = self.connect()
        logger.info("Deleting message: %s", message_id)
        
        # Get conversation_id before deleting
        cursor = conn.execute(
            "SELECT conversation_id FROM chat_messages WHERE message_id = ?",
            (message_id,)
        )
        row = cursor.fetchone()

        if not row:
            return False

        conversation_id = row['conversation_id']

        # Ownership check: ensure current user owns the conversation (if session present)
        current_user = self._get_current_user()
        if current_user:
            conv_user = self._conversation_user_id(conn, conversation_id)
            if conv_user and conv_user != current_user:
                logger.warning("Access denied to delete message %s for user %s", message_id, current_user)
                return False
        
        # Delete message
        cursor = conn.execute(
            "DELETE FROM chat_messages WHERE message_id = ?",
            (message_id,)
        )
        
        # Update conversation message count
        conn.execute("""
            UPDATE conversations
            SET message_count = message_count - 1
            WHERE conversation_id = ?
        """, (conversation_id,))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info("Message %s deleted", message_id)
            return True
        return False
    
    async def get_tool_call_history(self, endpoint: Optional[str] = None) -> List[ChatMessageRecord]:
        """
        Get history of tool calls, optionally filtered by endpoint.
        
        Args:
            endpoint: Optional endpoint name to filter by
        
        Returns:
            List[ChatMessageRecord]: List of tool call message records
        """
        conn = self.connect()
        logger.debug("Fetching tool call history (endpoint: %s)", endpoint)
        
        # If a session user is available, only return tool calls for that user's conversations
        current_user = self._get_current_user()
        if current_user:
            if endpoint:
                cursor = conn.execute("""
                    SELECT cm.* FROM chat_messages cm
                    JOIN conversations c ON cm.conversation_id = c.conversation_id
                    WHERE cm.message_type = 'tool_call' AND cm.tool_call_endpoint = ? AND c.userId = ?
                    ORDER BY cm.timestamp DESC
                """, (endpoint, current_user))
            else:
                cursor = conn.execute("""
                    SELECT cm.* FROM chat_messages cm
                    JOIN conversations c ON cm.conversation_id = c.conversation_id
                    WHERE cm.message_type = 'tool_call' AND c.userId = ?
                    ORDER BY cm.timestamp DESC
                """, (current_user,))
        else:
            if endpoint:
                cursor = conn.execute("""
                    SELECT * FROM chat_messages
                    WHERE message_type = 'tool_call' AND tool_call_endpoint = ?
                    ORDER BY timestamp DESC
                """, (endpoint,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM chat_messages
                    WHERE message_type = 'tool_call'
                    ORDER BY timestamp DESC
                """)
        
        messages = []
        for row in cursor.fetchall():
            messages.append(self._message_row_to_record(row))
        
        logger.info("Fetched %d tool calls", len(messages))
        return messages
    
    async def get_tool_call_by_id(self, message_id: str) -> Optional[ChatMessageRecord]:
        """
        Get a tool call message by ID.
        
        Convenience method to get a tool call for re-running.
        
        Args:
            message_id: Message unique identifier
        
        Returns:
            Optional[ChatMessageRecord]: Tool call message record if found, None otherwise
        """
        # get_message enforces ownership now
        message = await self.get_message(message_id)
        if message and message.message_type == 'tool_call':
            return message
        return None
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite Row to dictionary."""
        result = dict(row)
        
        # Parse JSON fields
        if result.get('metadata'):
            try:
                result['metadata'] = json.loads(result['metadata'])
            except json.JSONDecodeError:
                result['metadata'] = {}
        
        return result
    
    def _message_row_to_record(self, row: sqlite3.Row) -> ChatMessageRecord:
        """Convert SQLite Row to ChatMessageRecord."""
        data = dict(row)
        
        # Parse JSON fields
        if data.get('tool_calls'):
            try:
                data['tool_calls'] = json.loads(data['tool_calls'])
            except json.JSONDecodeError:
                data['tool_calls'] = None
        
        if data.get('tool_call_arguments'):
            try:
                data['tool_call_arguments'] = json.loads(data['tool_call_arguments'])
            except json.JSONDecodeError:
                data['tool_call_arguments'] = None
        
        if data.get('metadata'):
            try:
                data['metadata'] = json.loads(data['metadata'])
            except json.JSONDecodeError:
                data['metadata'] = None
        
        return ChatMessageRecord(**data)


_chat_history_db: Optional[ChatHistoryDB] = None


def get_chat_history_db() -> ChatHistoryDB:
    """
    Get global ChatHistoryDB instance, initializing it if needed.
    
    Returns:
        ChatHistoryDB: Chat history database instance
    """
    global _chat_history_db
    
    if _chat_history_db is None:
        logger.info("Lazy-initializing chat history database")
        _chat_history_db = ChatHistoryDB()
        _chat_history_db.connect()
    
    return _chat_history_db

