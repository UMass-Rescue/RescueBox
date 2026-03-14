# NiceGUI Storage Integration Guide

## Overview

This document describes how to integrate NiceGUI's built-in storage features with the current SQLite-based persistence system for chat history and job management. NiceGUI provides session and user-specific storage that complements our persistent database storage.

## NiceGUI Storage Types

According to [NiceGUI storage documentation](https://nicegui.io/documentation/storage), NiceGUI provides three types of storage:

1. **`app.storage.user`** - User-specific storage (persists across browser sessions, tied to user ID)
2. **`app.storage.client`** - Client-side storage (browser-specific, cleared on cache clear)
3. **`app.storage.general`** - General application storage (shared across all users)

## Current Implementation

Currently, we use:
- **SQLite Database** (`chat_history_db.py`, `job_db.py`) for persistent, cross-session storage
- **In-memory state** in `ChatbotPage` class for conversation_id and messages
- **No NiceGUI storage** currently utilized

## Integration Strategy

### Hybrid Approach: SQLite + NiceGUI Storage

**SQLite Database** (Permanent Storage):
- All conversations and messages (persistent across sessions)
- Job records and history
- Tool call history for re-running

**NiceGUI Storage** (Session & User State):
- Current conversation_id per user session
- UI preferences (dark mode, layout, etc.)
- Temporary UI state (form drafts, scroll positions)
- User-specific settings

### 1. User Identification

NiceGUI automatically assigns a unique user ID accessible via:
```python
from nicegui import app

user_id = app.storage.user.id  # Unique identifier per user session
```

**Integration with SQLite:**
- Store user_id in conversations table for multi-user support
- Link conversations to NiceGUI user IDs
- Enable user-specific conversation filtering

### 2. Current Conversation State

**Problem**: Currently, `conversation_id` is stored in `ChatbotPage` instance, which is lost on page refresh or navigation.

**Solution**: Use `app.storage.user` to persist the current conversation_id:

```python
from nicegui import app

# In ChatbotPage.__init__:
def __init__(self, ...):
    # Load conversation_id from NiceGUI storage, or create new one
    self.conversation_id = app.storage.user.get('current_conversation_id')
    if not self.conversation_id:
        # Create new conversation in database
        conversation = await chat_history.create_conversation()
        self.conversation_id = conversation.conversation_id
        app.storage.user['current_conversation_id'] = self.conversation_id
```

### 3. UI Preferences

Store user preferences in `app.storage.user`:

```python
# Store UI preferences
app.storage.user['preferences'] = {
    'dark_mode': False,
    'compact_view': False,
    'auto_scroll': True,
    'message_timestamp_format': 'relative'  # 'relative' or 'absolute'
}

# Retrieve preferences
preferences = app.storage.user.get('preferences', {
    'dark_mode': False,
    'compact_view': False,
    'auto_scroll': True,
    'message_timestamp_format': 'relative'
})
```

### 4. Temporary UI State

Use `app.storage.client` for browser-specific temporary state:

```python
# Store draft messages (cleared when browser cache is cleared)
app.storage.client['draft_message'] = "Find faces in..."

# Store scroll position
app.storage.client['chat_scroll_position'] = 500

# Store form draft data
app.storage.client['form_draft'] = {
    'endpoint': 'face-detection/findface',
    'arguments': {'input_dir': '/tmp'}
}
```

### 5. Multi-User Support in SQLite

Update database schema to support user identification:

**Update `chat_history_db.py`:**

```python
class ConversationRecord(BaseModel):
    conversation_id: str
    user_id: Optional[str] = None  # NiceGUI user ID
    title: str
    created_at: str
    updated_at: str
    message_count: int
    metadata: Optional[Dict[str, Any]] = None
```

**Update database schema:**

```sql
ALTER TABLE conversations ADD COLUMN user_id TEXT;
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
```

**Update methods to filter by user_id:**

```python
async def get_all_conversations(self, user_id: Optional[str] = None) -> List[ConversationRecord]:
    """Get conversations, optionally filtered by user_id"""
    conn = self.connect()
    
    if user_id:
        cursor = conn.execute("""
            SELECT * FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))
    else:
        cursor = conn.execute("""
            SELECT * FROM conversations
            ORDER BY updated_at DESC
        """)
    
    # ... rest of implementation
```

## Implementation Plan

### Phase 1: Basic Integration

1. **Update ChatbotPage to use NiceGUI storage for conversation_id**
   - Store current conversation_id in `app.storage.user`
   - Load conversation_id on page initialization
   - Save conversation_id when creating new conversations

2. **Add user_id support to database**
   - Update ConversationRecord model
   - Update database schema (add user_id column)
   - Update create_conversation to accept user_id

### Phase 2: User Preferences

3. **Implement user preferences storage**
   - Create preferences management utility
   - Store/load preferences from `app.storage.user`
   - Apply preferences to UI components

### Phase 3: Enhanced State Management

4. **Use client storage for temporary state**
   - Draft messages
   - Scroll positions
   - Form drafts

5. **Multi-user conversation filtering**
   - Update get_all_conversations to filter by user_id
   - Update history panel to show only user's conversations

## Code Examples

### Example 1: Conversation ID Management

```python
# frontend/pages/chatbot.py
from nicegui import app
from frontend.database import get_chat_history_db

class ChatbotPage:
    def __init__(self, ...):
        # Initialize conversation_id from NiceGUI storage
        self._initialize_conversation()
    
    async def _initialize_conversation(self):
        """Initialize or load conversation from NiceGUI storage"""
        chat_history = get_chat_history_db()
        user_id = app.storage.user.id
        
        # Try to load current conversation from storage
        conversation_id = app.storage.user.get('current_conversation_id')
        
        if conversation_id:
            # Verify conversation exists and belongs to user
            conversation = await chat_history.get_conversation(conversation_id)
            if conversation and conversation.user_id == user_id:
                self.conversation_id = conversation_id
                logger.info(f"Loaded conversation {conversation_id} from storage")
                return
        
        # Create new conversation
        conversation = await chat_history.create_conversation(user_id=user_id)
        self.conversation_id = conversation.conversation_id
        app.storage.user['current_conversation_id'] = self.conversation_id
        logger.info(f"Created new conversation {self.conversation_id}")
    
    def new_conversation(self):
        """Start a new conversation and update storage"""
        # Create new conversation will be handled by _initialize_conversation
        # after clearing the current one
        app.storage.user['current_conversation_id'] = None
        self.conversation_id = None
        self.messages = []
        self.chat_container.clear()
        await self._initialize_conversation()
```

### Example 2: User Preferences

```python
# frontend/utils/user_preferences.py
"""
User preferences management using NiceGUI storage
"""
from nicegui import app
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

DEFAULT_PREFERENCES = {
    'dark_mode': False,
    'compact_view': False,
    'auto_scroll': True,
    'message_timestamp_format': 'relative',  # 'relative' or 'absolute'
    'notifications_enabled': True,
}

def get_user_preferences() -> Dict[str, Any]:
    """
    Get user preferences from NiceGUI storage.
    
    Returns:
        Dict with user preferences, using defaults if not set
    """
    preferences = app.storage.user.get('preferences', {})
    # Merge with defaults to ensure all keys exist
    return {**DEFAULT_PREFERENCES, **preferences}

def set_user_preference(key: str, value: Any):
    """
    Set a single user preference.
    
    Args:
        key: Preference key
        value: Preference value
    """
    preferences = get_user_preferences()
    preferences[key] = value
    app.storage.user['preferences'] = preferences
    logger.debug(f"Updated preference: {key} = {value}")

def set_user_preferences(new_preferences: Dict[str, Any]):
    """
    Update multiple user preferences at once.
    
    Args:
        new_preferences: Dictionary of preferences to update
    """
    preferences = get_user_preferences()
    preferences.update(new_preferences)
    app.storage.user['preferences'] = preferences
    logger.info(f"Updated {len(new_preferences)} preferences")

# Usage in ChatbotPage:
def render(self):
    preferences = get_user_preferences()
    if preferences['auto_scroll']:
        # Enable auto-scroll behavior
        pass
```

### Example 3: Draft Message Storage

```python
# In chatbot_ui.py - store draft message
def on_input_change(e):
    """Store draft message as user types"""
    app.storage.client['draft_message'] = e.value

# On page load - restore draft
async def chatbot_page():
    draft = app.storage.client.get('draft_message', '')
    if draft:
        # Pre-fill input field
        input_field.value = draft
```

### Example 4: Updated Database Methods

```python
# frontend/database/chat_history_db.py
async def create_conversation(
    self, 
    title: Optional[str] = None,
    user_id: Optional[str] = None
) -> ConversationRecord:
    """Create conversation with optional user_id"""
    conversation_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    title = title or f"Conversation {now[:10]}"
    
    conn = self.connect()
    logger.info(f"Creating conversation: {conversation_id} (user: {user_id})")
    
    conn.execute("""
        INSERT INTO conversations (conversation_id, user_id, title, created_at, updated_at, message_count)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (conversation_id, user_id, title, now, now))
    
    conn.commit()
    
    return ConversationRecord(
        conversation_id=conversation_id,
        user_id=user_id,
        title=title,
        created_at=now,
        updated_at=now,
        message_count=0
    )

async def get_all_conversations(
    self, 
    user_id: Optional[str] = None
) -> List[ConversationRecord]:
    """
    Get all conversations, optionally filtered by user_id.
    
    Args:
        user_id: Optional user ID to filter conversations
    
    Returns:
        List of conversation records
    """
    conn = self.connect()
    
    if user_id:
        cursor = conn.execute("""
            SELECT * FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))
    else:
        cursor = conn.execute("""
            SELECT * FROM conversations
            ORDER BY updated_at DESC
        """)
    
    conversations = []
    for row in cursor.fetchall():
        conversations.append(ConversationRecord(**self._row_to_dict(row)))
    
    return conversations
```

## Benefits of Integration

1. **Session Persistence**: Conversation state survives page refreshes
2. **User Preferences**: Per-user UI customization
3. **Multi-User Support**: Separate conversations per user session
4. **Temporary State**: Draft messages and UI state preservation
5. **Better UX**: Seamless experience across page navigations

## Migration Path

1. **Backward Compatibility**: Existing conversations without user_id still work (user_id can be NULL)
2. **Gradual Rollout**: Add NiceGUI storage features incrementally
3. **Default Behavior**: If no user_id, show all conversations (current behavior)
4. **Future Enhancement**: Add user authentication to link NiceGUI user IDs to real users

## Security Considerations

- **User ID Isolation**: Ensure users can only see their own conversations
- **Storage Limits**: NiceGUI storage has size limits; use SQLite for large data
- **Sensitive Data**: Never store sensitive information in client storage
- **Session Security**: Use `storage_secret` when integrating with FastAPI (see NiceGUI docs)

## References

- [NiceGUI Storage Documentation](https://nicegui.io/documentation/storage)
- Current implementation: `frontend/database/chat_history_db.py`
- Current chatbot: `frontend/pages/chatbot.py`

