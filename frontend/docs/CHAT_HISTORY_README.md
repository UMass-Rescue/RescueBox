# Chat History Persistence Design

## Overview

This document describes the design for persisting chat conversation history in the SQLite database, including user prompts, assistant responses, and tool calls. The system enables users to recall previous conversations and re-run tool calls from history.

## Database Schema

### `conversations` Table

Stores conversation metadata and grouping information.

| Column | Type | Description |
|--------|------|-------------|
| `conversation_id` | TEXT PRIMARY KEY | Unique conversation identifier (UUID) |
| `title` | TEXT | Conversation title (auto-generated from first message) |
| `created_at` | TEXT NOT NULL | Conversation creation timestamp (ISO format) |
| `updated_at` | TEXT NOT NULL | Last update timestamp (ISO format) |
| `message_count` | INTEGER | Number of messages in conversation |
| `metadata` | TEXT | Additional metadata as JSON (optional) |

### `chat_messages` Table

Stores individual messages within conversations.

| Column | Type | Description |
|--------|------|-------------|
| `message_id` | TEXT PRIMARY KEY | Unique message identifier (UUID) |
| `conversation_id` | TEXT NOT NULL | Foreign key to conversations table |
| `role` | TEXT NOT NULL | Message role: 'user' or 'assistant' |
| `content` | TEXT NOT NULL | Message text content |
| `message_type` | TEXT | Message type: 'text', 'tool_call', 'tool_result', 'error' |
| `tool_calls` | TEXT | Tool calls as JSON (for assistant messages with tool calls) |
| `tool_call_endpoint` | TEXT | Endpoint name from tool call (for easy filtering) |
| `tool_call_arguments` | TEXT | Tool call arguments as JSON |
| `timestamp` | TEXT NOT NULL | Message timestamp (ISO format) |
| `metadata` | TEXT | Additional metadata as JSON (optional) |

**Indexes:**
- `idx_chat_messages_conversation_id` on `conversation_id`
- `idx_chat_messages_timestamp` on `timestamp`
- `idx_chat_messages_tool_call_endpoint` on `tool_call_endpoint`

## Data Models

### ConversationRecord (Pydantic)

```python
class ConversationRecord(BaseModel):
    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    metadata: Optional[Dict[str, Any]] = None
```

### ChatMessageRecord (Pydantic)

```python
class ChatMessageRecord(BaseModel):
    message_id: str
    conversation_id: str
    role: str  # 'user' or 'assistant'
    content: str
    message_type: str = 'text'  # 'text', 'tool_call', 'tool_result', 'error'
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_endpoint: Optional[str] = None
    tool_call_arguments: Optional[Dict[str, Any]] = None
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
```

## API Design

### ChatHistoryDB Class

```python
class ChatHistoryDB:
    """Manages chat conversation history in SQLite database"""
    
    # Conversation Management
    async def create_conversation(title: Optional[str] = None) -> ConversationRecord
    async def get_conversation(conversation_id: str) -> Optional[ConversationRecord]
    async def get_all_conversations() -> List[ConversationRecord]
    async def update_conversation(conversation_id: str, **updates) -> bool
    async def delete_conversation(conversation_id: str) -> bool
    
    # Message Management
    async def add_message(
        conversation_id: str,
        role: str,
        content: str,
        message_type: str = 'text',
        tool_calls: Optional[List[Dict]] = None,
        tool_call_endpoint: Optional[str] = None,
        tool_call_arguments: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> ChatMessageRecord
    
    async def get_messages(conversation_id: str) -> List[ChatMessageRecord]
    async def get_message(message_id: str) -> Optional[ChatMessageRecord]
    async def delete_message(message_id: str) -> bool
    
    # Tool Call History
    async def get_tool_call_history(endpoint: Optional[str] = None) -> List[ChatMessageRecord]
    async def get_tool_call_by_id(message_id: str) -> Optional[ChatMessageRecord]
```

## Integration Points

### 1. Chatbot Message Handling

**Location**: `frontend/pages/chatbot_handlers.py`

**Changes**:
- Save user messages when sent
- Save assistant responses (text and tool calls)
- Link messages to conversation_id

**Example**:
```python
async def handle_send_message(...):
    # ... existing code ...
    
    # Save user message
    chat_history = get_chat_history_db()
    if not conversation_id:
        conversation = await chat_history.create_conversation()
        conversation_id = conversation.conversation_id
    
    await chat_history.add_message(
        conversation_id=conversation_id,
        role='user',
        content=message_text
    )
    
    # ... process message ...
    
    # Save assistant response
    if result['type'] == 'tool_calls':
        for tool_call in result['content']:
            await chat_history.add_message(
                conversation_id=conversation_id,
                role='assistant',
                content=f"Selected tool: {tool_call['name']}",
                message_type='tool_call',
                tool_calls=[tool_call],
                tool_call_endpoint=tool_call['name'],
                tool_call_arguments=tool_call.get('arguments', {})
            )
```

### 2. Tool Call Execution

**Location**: `frontend/pages/chatbot_handlers.py` (handle_form_submit)

**Changes**:
- Save tool call execution results
- Link tool results to original tool call message

**Example**:
```python
async def handle_form_submit(...):
    # ... existing code ...
    
    # Save tool call result
    await chat_history.add_message(
        conversation_id=conversation_id,
        role='assistant',
        content="Job completed successfully",
        message_type='tool_result',
        tool_call_endpoint=endpoint,
        metadata={'job_id': job.uid, 'status': 'completed'}
    )
```

### 3. Chatbot UI - History Panel

**New Component**: `frontend/components/chat_history_panel.py`

**Features**:
- List of previous conversations
- Search/filter conversations
- View conversation messages
- Re-run tool calls from history

**UI Layout**:
```
┌─────────────────────────────────────┐
│ Chat History                        │
├─────────────────────────────────────┤
│ [🔍 Search conversations...]        │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 📝 Find faces in images         │ │
│ │   2 hours ago • 5 messages      │ │
│ │   [View] [Re-run last tool]     │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 📝 Summarize photos             │ │
│ │   1 day ago • 3 messages        │ │
│ │   [View] [Re-run last tool]     │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 4. Re-run Mechanism

**Location**: `frontend/pages/chatbot_forms.py` or new `chatbot_history.py`

**Functionality**:
- Load tool call from history
- Pre-fill form with previous arguments
- Submit to same endpoint
- Create new job record

**Flow**:
1. User clicks "Re-run" on a tool call in history
2. Load tool call details (endpoint, arguments)
3. Fetch current task schema for endpoint
4. Show form pre-filled with previous arguments
5. User can modify or submit as-is
6. Submit creates new job (new job_id, new timestamp)

## Usage Examples

### Creating a Conversation

```python
from frontend.database import get_chat_history_db

chat_history = get_chat_history_db()

# Auto-create conversation on first message
conversation = await chat_history.create_conversation()
conversation_id = conversation.conversation_id
```

### Saving Messages

```python
# Save user message
await chat_history.add_message(
    conversation_id=conversation_id,
    role='user',
    content="Find faces in my images"
)

# Save assistant tool call
await chat_history.add_message(
    conversation_id=conversation_id,
    role='assistant',
    content="I'll use the face detection tool",
    message_type='tool_call',
    tool_calls=[{
        'name': 'face-detection/findface',
        'arguments': {'input_dir': '/path/to/images'}
    }],
    tool_call_endpoint='face-detection/findface',
    tool_call_arguments={'input_dir': '/path/to/images'}
)
```

### Loading Conversation History

```python
# Get all conversations
conversations = await chat_history.get_all_conversations()

# Get messages for a conversation
messages = await chat_history.get_messages(conversation_id)

# Get tool call history
tool_calls = await chat_history.get_tool_call_history(
    endpoint='face-detection/findface'  # Optional filter
)
```

### Re-running a Tool Call

```python
# Get tool call from history
tool_call_msg = await chat_history.get_tool_call_by_id(message_id)

# Extract endpoint and arguments
endpoint = tool_call_msg.tool_call_endpoint
arguments = tool_call_msg.tool_call_arguments

# Load form and pre-fill
await load_and_show_form(
    container=chat_container,
    core=core,
    endpoint=endpoint,
    arguments=arguments,
    on_form_submit=form_submit_handler
)
```

## UI Components

### 1. History Sidebar

**Component**: `frontend/components/chat_history_panel.py`

**Features**:
- Collapsible sidebar panel
- List of conversations with preview
- Search/filter functionality
- Click to load conversation
- Re-run button for tool calls

### 2. Conversation View

**Component**: `frontend/pages/chatbot_history.py` (new page)

**Features**:
- Full conversation display
- Message timeline
- Tool call details
- Re-run buttons on tool calls
- Export conversation

### 3. In-Chat History Integration

**Enhancement**: `frontend/pages/chatbot_ui.py`

**Features**:
- "History" button in chat header
- Quick access to recent tool calls
- "Re-run last tool" button

## Database File

The chat history is stored in the same database file as jobs:
```
frontend/data/jobs.db
```

Both `jobs` and `conversations`/`chat_messages` tables coexist in the same database.

## Migration Strategy

1. **Phase 1**: Create database schema and models
2. **Phase 2**: Integrate message saving in chatbot handlers
3. **Phase 3**: Create history UI components
4. **Phase 4**: Add re-run functionality
5. **Phase 5**: Add search and filtering

## Benefits

1. **Persistent History**: All conversations saved automatically
2. **Easy Recall**: Quick access to previous interactions
3. **Re-run Capability**: Re-execute tool calls with same or modified parameters
4. **Learning Tool**: Users can see what worked before
5. **Debugging**: Review conversation flow for troubleshooting

## Future Enhancements

1. **Export Conversations**: Export to JSON/CSV
2. **Conversation Sharing**: Share conversation links
3. **Favorites**: Mark important conversations
4. **Tags**: Tag conversations for organization
5. **Search**: Full-text search across conversations
6. **Analytics**: Track tool usage patterns

