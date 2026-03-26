┌────────────────────────────────────────┐
│ 🤖 Assistant              10:38 AM     │
│                                         │
│ ✅ Job Completed!                       │
│                                         │
│ ┌───────────────────────────────────┐ │
│ │ 📊 Results                        │ │
│ │                                   │ │
│ │ Summary:                          │ │
│ │ • 24 images processed            │ │
│ │ • 47 faces detected              │ │
│ │ • Output: /output/job-123/       │ │
│ │                                   │ │
│ │ Preview:                          │ │
│ │ ┌─────┬─────┬─────┬─────┐       │ │
│ │ │ 🖼️ │ 🖼️ │ 🖼️ │ 🖼️ │       │ │
│ │ │img1 │img2 │img3 │img4 │       │ │
│ │ └─────┴─────┴─────┴─────┘       │ │
│ │                                   │ │
│ │ [👁️ View Full] [📂 Folder]       │ │
│ │ [🔄 Run Again] [📋 Details]       │ │
│ └───────────────────────────────────┘ │
└────────────────────────────────────────┘


┌────────────────────────────────────────┐
│ Attachments:                           │
│ [📁 /documents/photos (24 files) ×]   │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Type your request...               │ │
│ │                                    │ │
│ │                                    │ │
│ └────────────────────────────────────┘ │
│                                        │
│ 💡 Suggestions:                        │
│ • Detect faces in images               │
│ • Transcribe audio files               │
│                                        │
│                    [📎 Attach] [▶ Send]│
└────────────────────────────────────────┘

┌──────────────────────┐
│ 📊 Recent Results    │
│ ┌──────────────────┐ │
│ │ 🔍 Face Detect   │ │
│ │   2 hours ago    │ │
│ │   ✅ Completed   │ │
│ │   [View]         │ │
│ └──────────────────┘ │
│ ┌──────────────────┐ │
│ │ 🎵 Audio Trans   │ │
│ │   1 day ago      │ │
│ │   ✅ Completed   │ │
│ │   [View]         │ │
│ └──────────────────┘ │
└──────────────────────┘


┌────────────────────────────────────────┐
│ 🤖 Assistant                           │
│                                         │
│ Here are your recent face detection    │
│ results:                               │
│                                         │
│ ┌───────────────────────────────────┐ │
│ │ 📊 Previous Job (2 hours ago)     │ │
│ │ • 24 faces detected               │ │
│ │ • Model: face-detection v3.0      │ │
│ │ [👁️ View] [🔄 Re-run]             │ │
│ └───────────────────────────────────┘ │
└────────────────────────────────────────┘

User Flows
Flow 1: Basic Query → Tool Selection → Form → Execution

**Note**: This flow now supports multiple tool calls. When the Granite model returns multiple tool calls (e.g., "summarize photos and detect fakes"), they execute sequentially with automatic output chaining. See Flow 1A for multiple tool call details.

1. User opens Assistant page
   State: Idle
   UI: Empty chat with input field

2. User types: "Find faces in my images"
   Action: onSend(message)
   State: Processing

3. Frontend sends to backend
   API: POST /agent/chat
   Payload: { message: "...", conversationId: null }

4. Backend processes query
   - Agent plugin receives
   - Discovers available tools via backend aggregation endpoints
   - Sends to Granite LLM
   - LLM returns tool selection with endpoint name and arguments
   Note: Tool calls now use format { name: "endpoint", arguments: {...} }
         instead of modelUid/taskUid structure

5. Backend responds
   Response: {
     toolName: "face-detection/findface",
     toolSchema: TaskSchema,  // Retrieved via GET /{endpoint}/task_schema
   
   Note: Assistant response and tool call are automatically saved to chat history
   Database: ChatHistoryDB.add_message(
     conversation_id, 
     role='assistant', 
     message_type='tool_call',
     tool_call_endpoint=endpoint,
     tool_call_arguments=arguments
   )
     suggestedInputs: {...}
   }
   State: ToolSelected

6. Frontend displays tool selection
   Component: ToolSelectionMessage
   UI: Shows selected tool card

7. Frontend fetches full schema
   API: GET /{endpoint}/task_schema
   Where endpoint is extracted from tool call name (e.g., "face-detection/findface")
   State: LoadingForm

8. Frontend renders input form
   Component: InputFormMessage
   UI: Dynamic form with fields
   State: AwaitingInput

9. User fills form
   - Selects directory
   - Adjusts parameters
   Action: Form state updates
   State: FormReady

10. User submits form
    Action: onSubmit(formData)
    API: POST /{endpoint}
    Payload: {
      // Direct endpoint call with arguments
      ...formData  // arguments from tool call
    }
    Note: For chatbot jobs, endpoint is used directly (no modelUid/taskUid).
          For traditional jobs, POST /jobs is still used with modelUid/taskUid.
    State: JobSubmitted

11. Frontend displays job status
    Component: JobStatusMessage
    UI: Progress bar, status text
    State: JobRunning

12. Frontend polls job status
    API: GET /jobs/{jobId} (polling)
    OR: WebSocket updates
    State: JobRunning (updates)

13. Job completes
    API Response: { status: "Completed", response: {...} }
    State: JobCompleted

14. Frontend displays results
    Component: ResultsMessage
    UI: Results preview with actions
    State: ResultsDisplayed
    
    Note: Tool call result is automatically saved to chat history
    Database: ChatHistoryDB.add_message(
      conversation_id,
      role='assistant',
      message_type='tool_result',
      tool_call_endpoint=endpoint,
      metadata={'job_id': job_uid, 'status': 'completed'}
    )

15. User can interact with results
    Actions:
    - View Full: Navigate to /jobs/{jobId}/outputs
    - Open Folder: Open file explorer
    - Run Again: Pre-fill form
    State: Idle (ready for next query)

Flow 2: Query with Attachments

1. User attaches directory before typing
   Action: onAttach(directory)
   State: AttachmentAdded
   UI: Shows attachment chip

2. User types: "Analyze these"
   Action: onSend(message, [attachment])
   Payload: {
     message: "Analyze these",
     attachments: [{ type: "directory", path: "..." }]
   }

3. Backend receives query + attachments
   - LLM considers attached files in context
   - Selects appropriate tool

4. Form is pre-filled with attachment
   Component: InputFormMessage
   Props: initialValues={{ input_dir: attachment.path }}
   UI: Directory field already filled

5. User adjusts parameters and submits
   [Continues as Flow 1 from step 10]
   
Flow 3: Re-running Previous Job

1. User views previous results
   Component: PreviousResults
   Action: onSelectResult(jobId)
   Note: Jobs are stored in local SQLite database (JobDB)

2. User clicks "Run Again"
   Action: onRerun(jobId)
   API: Load from local database or GET /jobs/{jobId}

3. Frontend retrieves job details
   Response (from JobDB or API): {
     uid: "...",
     endpoint: "...",  // For chatbot jobs
     modelUid: "...",  // For traditional jobs (optional)
     taskUid: "...",   // For traditional jobs (optional)
     request: {...},   // Original request data
     taskSchema: {...} // Saved schema for form regeneration
   }

4. Frontend creates new message
   Component: InputFormMessage
   Props: initialValues={jobData.request, schema=jobData.taskSchema}
   UI: Pre-filled form in chat

5. User can modify or submit as-is
   - If endpoint exists: POST /{endpoint}
   - If modelUid/taskUid exists: POST /jobs
   [Continues as Flow 1 from step 9]
   
Flow 4: Chat History - View and Re-run

1. User clicks "📜 History" button
   Action: show_history_dialog()
   UI: History panel dialog opens

2. History panel displays conversations
   API: ChatHistoryDB.get_all_conversations()
   UI: List of conversations with titles, timestamps, message counts

3. User selects a conversation
   Action: view_conversation(conversation_id)
   API: ChatHistoryDB.get_messages(conversation_id)
   UI: Full conversation displayed in dialog with messages

4. User clicks "Re-run" on a tool call
   Action: rerun_tool_call(message_id)
   API: ChatHistoryDB.get_tool_call_by_id(message_id)
   Navigation: ui.navigate.to(f'/chatbot?rerun={message_id}')

5. Chatbot page loads with re-run parameter
   Route: /chatbot?rerun=message_id
   Action: Load tool call from history
   API: ChatHistoryDB.get_tool_call_by_id(message_id)
   Result: Form pre-filled with previous arguments

6. User can modify or submit as-is
   [Continues as Flow 1 from step 9]

Flow 5: Error Handling Flow
1. User submits query
   [Normal flow until step 4]

2. LLM fails to select tool
   Response: { error: "No suitable tool found" }
   State: Error
   Component: ErrorMessage
   UI: Error message with suggestions

3. User adjusts query and retries
   Action: onRetry(adjustedMessage)
   [Returns to Flow 1 step 2]

---

1. User submits form
   [Normal flow until step 10]

2. Form validation fails
   Action: validateForm(data, schema)
   Result: { isValid: false, errors: {...} }
   UI: Error messages on fields
   State: ValidationError

3. User fixes errors and resubmits
   [Returns to Flow 1 step 9]

---

1. Job execution fails
   [Normal flow until step 12]

2. Job status becomes "Failed"
   Response: { status: "Failed", error: "..." }
   State: JobFailed
   Component: ErrorMessage (in JobStatusMessage)
   UI: Error display with retry option

3. User can retry with same inputs
   Action: onRetry()
   [Creates new job with same data]

---

## Backend API Integration

### Model and Server Discovery

**Models Page Flow:**

1. Page loads
   API: GET /models
   Returns: List of all registered plugins as models
   Response: [
     {
       "uid": "audio_transcription",
       "name": "Audio transcription library",
       "plugin_name": "audio_transcription",
       "version": "3.0.0",
       "author": "Rescue Lab",
       "info": "Markdown documentation...",
       "gpu": false
     },
     ...
   ]

2. Fetch server statuses
   API: GET /servers
   Returns: List of server entries (one per plugin)
   Response: [
     {
       "modelUid": "audio_transcription",
       "serverAddress": "localhost",
       "serverPort": 8000,
       "isUserConnected": true,
       "pluginName": "audio_transcription"
     },
     ...
   ]

3. Check individual server status
   API: GET /servers/{model_uid}/status
   Returns: Server status for specific model
   Response: {
     "status": "Online",  // All plugins are "Online" by default (served by same backend)
     "modelUid": "audio_transcription",
     "serverAddress": "localhost",
     "serverPort": 8000,
     "isUserConnected": true,
     "pluginName": "audio_transcription"
   }

**Model Details Page Flow:**

1. Navigate to model details
   Route: /models/{model_uid}/details

2. Fetch model metadata
   API: GET /models/{model_uid}/info (or GET /models/{model_uid})
   Returns: Model metadata
   Response: {
     "uid": "audio_transcription",
     "name": "Audio transcription library",
     "plugin_name": "audio_transcription",
     "version": "3.0.0",
     "author": "Rescue Lab",
     "info": "Markdown documentation...",
     "gpu": false
   }

3. Check server status
   API: GET /servers/{model_uid}/status
   Returns: Current server status

### Backend Aggregation Endpoints

The backend now provides aggregation endpoints that discover plugins dynamically:

- **GET /models** - Aggregates all registered plugins into a unified models list
- **GET /models/{model_uid}** - Returns specific plugin metadata
- **GET /models/{model_uid}/info** - Alias for /models/{model_uid}
- **GET /servers** - Returns server entries (one per plugin)
- **GET /servers/{model_uid}/status** - Returns server status for a plugin

All plugins are served by the same backend server (default: localhost:8000, configurable via `RESCUEBOX_API_URL` environment variable), so they are all "Online" by default.

### Tool Call Format Changes

**Old Format (deprecated):**
```json
{
  "modelUid": "face-detection",
  "taskUid": "findface",
  "arguments": {...}
}
```

**New Format (current):**
```json
{
  "name": "face-detection/findface",
  "arguments": {...}
}
```

The `name` field is the FastAPI endpoint path, and `arguments` are the input parameters.

### Job Storage

Jobs are stored in local SQLite database (JobDB):
- Chatbot-created jobs: Saved with `endpoint` field
- Traditional jobs: Saved with `modelUid` and `taskUid` fields
- All jobs include: `taskSchema`, `request`, `response`, `status`, timestamps


### API Endpoints Summary

| Endpoint | Method | Purpose | Frontend Usage |
|----------|--------|---------|----------------|
| `/models` | GET | List all models (plugins) | Models page - fetch all available models |
| `/models/{model_uid}` | GET | Get model metadata | Model details page, Job pages |
| `/models/{model_uid}/info` | GET | Get model info (alias) | Model details page (fallback) |
| `/servers` | GET | List all servers | Models page - check server statuses |
| `/servers/{model_uid}/status` | GET | Get server status | Models page - check individual status |
| `/{endpoint}/task_schema` | GET | Get task schema for endpoint | Chatbot - fetch form schema |
| `/{endpoint}` | POST | Submit job to endpoint | Chatbot - submit form data |
| `/agent/chat` | POST | Chat with agent | Chatbot - send messages, get tool calls |

For detailed API documentation, see `docs/BACKEND_API_CALLS.md` and `docs/API_CALLS_SUMMARY.md`.

## Frontend Architecture Updates (2024 Refactoring)

### Centralized Configuration
- **File**: `frontend/config.py`
- **Purpose**: All configuration values centralized with environment variable support
- **Usage**: `from frontend.config import API_BASE_URL, APP_PORT`
- **Benefits**: Easy to override via environment variables (e.g., `RESCUEBOX_API_URL`, `RESCUEBOX_PORT`)

### Shared API Client
- **File**: `frontend/api_client.py`
- **Purpose**: Single API client instance shared across all components
- **Usage**: `from frontend.api_client import api_client` then `await api_client.client.get('/models')`
- **Benefits**: Consistent base URL, timeout, and error handling across all API calls
- **Note**: All pages now use the shared `api_client` instead of creating individual `httpx.AsyncClient` instances

### Standardized Error Handling
- **File**: `frontend/utils/error_handling.py`
- **Purpose**: Consistent error handling patterns
- **Usage**: `from frontend.utils.error_handling import handle_api_error` then `await handle_api_error(e, "Error loading models")`
- **Benefits**: Unified error logging and user notifications

### Path Setup Utilities
- **File**: `frontend/utils/path_setup.py`
- **Purpose**: Centralized backend path setup for imports
- **Usage**: `from frontend.utils.path_setup import setup_backend_path` then `setup_backend_path()`
- **Benefits**: Eliminates duplicate `sys.path.insert` code across files

### Application Constants
- **File**: `frontend/constants.py`
- **Purpose**: Centralized UI strings, status messages, error messages
- **Usage**: `from frontend.constants import UI_TITLES, UI_BUTTONS, ERROR_MESSAGES`
- **Benefits**: Consistent terminology, easier to update, enables future internationalization

### Results Renderers Refactoring

The results rendering system has been refactored into specialized modules for better maintainability:

#### Module Structure
- **`results_renderers.py`**: Facade module that re-exports all renderer functions for backward compatibility
- **`table_helpers.py`**: Reusable table utilities including:
  - `create_sortable_table()`: Creates NiceGUI sortable tables with common styling
  - `create_metadata_table_columns()`: Generates table columns from metadata keys
  - `create_file_row_click_handler()`: Handles file row clicks for opening files
  - `create_directory_row_click_handler()`: Handles directory row clicks for opening folders
- **`file_renderers.py`**: File response rendering:
  - `render_file()`: Single file response (images preview inline, others show buttons)
  - `render_batch_file()`: Batch file response with sortable metadata table
- **`directory_renderers.py`**: Directory response rendering:
  - `render_directory()`: Single directory response with sortable file listing
  - `render_batch_directory()`: Batch directory response with sortable table
- **`text_renderers.py`**: Text response rendering:
  - `render_text()`: Text response (detects JSON arrays of file paths for searchable display)
  - `render_markdown()`: Markdown response with formatted display
  - `render_batch_text()`: Batch text response with sortable table

#### Enhanced Features
- **Sortable Tables**: All batch responses and directory listings use NiceGUI's `ui.table` with sortable columns
- **Searchable Content**: Text responses containing JSON arrays of file paths are rendered in a searchable, filterable table
- **Clickable Paths**: File and directory paths in tables are clickable to open in file explorer
- **Metadata Columns**: Batch file responses with metadata automatically generate columns for each metadata key

#### Testing
Comprehensive unit tests for all renderer modules:
- `test_table_helpers.py`: Tests for table utility functions
- `test_file_renderers.py`: Tests for file rendering (single and batch)
- `test_directory_renderers.py`: Tests for directory rendering (single and batch)
- `test_text_renderers.py`: Tests for text rendering (text, markdown, batch, searchable lists)
- `test_components.py`: Updated to test ResultsPreview integration with new renderers

### Migration Impact

**Before Refactoring:**
- Hardcoded `base_url='http://localhost:8000'` in multiple files
- Duplicate `sys.path.insert` in 18+ files
- Inconsistent error handling patterns
- Hardcoded UI strings throughout codebase
- Duplicate navbar function in `main.py`
- Large `results_renderers.py` file (~467 lines) handling all rendering logic

**After Refactoring:**
- Centralized configuration via `config.py`
- Shared API client via `api_client.py`
- Standardized error handling via `utils/error_handling.py`
- Centralized path setup via `utils/path_setup.py`
- Application constants via `constants.py`
- All major pages updated to use new patterns
- Results renderers split into focused modules:
  - `table_helpers.py` (~160 lines) - Reusable utilities
  - `file_renderers.py` (~208 lines) - File-specific rendering
  - `directory_renderers.py` (~170 lines) - Directory-specific rendering
  - `text_renderers.py` (~305 lines) - Text-specific rendering
  - `results_renderers.py` (~39 lines) - Facade for backward compatibility
- Enhanced UI features (sortable tables, searchable content, clickable paths)

For detailed refactoring documentation, see `docs/REFACTORING_COMPLETE.md`.

## Chat History Persistence

### Automatic Message Saving

All chat interactions are automatically persisted to the SQLite database:

1. **User Messages**: Saved when sent via `handle_send_message()`
2. **Assistant Responses**: Saved when received from backend
3. **Tool Calls**: Saved with endpoint and arguments for re-running
4. **Tool Results**: Saved when job completes (success or failure)

### Database Schema

**Conversations Table:**
- `conversation_id` (PRIMARY KEY): Unique conversation identifier
- `title`: Conversation title (auto-generated from first message)
- `created_at`, `updated_at`: Timestamps
- `message_count`: Number of messages in conversation
- `metadata`: Additional metadata as JSON

**Chat Messages Table:**
- `message_id` (PRIMARY KEY): Unique message identifier
- `conversation_id` (FOREIGN KEY): Links to conversations table
- `role`: 'user' or 'assistant'
- `content`: Message text content
- `message_type`: 'text', 'tool_call', 'tool_result', 'error'
- `tool_calls`: Tool calls as JSON (for assistant messages)
- `tool_call_endpoint`: Endpoint name (for filtering)
- `tool_call_arguments`: Tool call arguments as JSON
- `timestamp`: Message timestamp
- `metadata`: Additional metadata as JSON

### History Access

**Via UI:**
- Click "📜 History" button in chatbot header
- View conversations list with search
- Click "View" to see full conversation
- Click "Re-run" on tool calls to execute again

**Via URL:**
- Navigate to `/chatbot?rerun=message_id` to re-run a tool call
- Form will be pre-filled with previous arguments

### Re-run Flow

1. User clicks "Re-run" on a tool call in history
2. System loads tool call details (endpoint, arguments)
3. Fetches current task schema for endpoint
4. Shows form pre-filled with previous arguments
5. User can modify or submit as-is
6. Creates new job (new job_id, new timestamp)

For detailed chat history documentation, see `docs/CHAT_HISTORY_README.md`.