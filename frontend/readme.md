# RescueBox Desktop - NiceGUI Frontend Design Document

**Up-to-date documentation:** [`docs/README.md`](docs/README.md) (workflow, theme, chat history, jobs, database, results, pipeline/filter, testing). The sections below mix **implemented behavior** with older design notes—when in doubt, trust **`docs/`** and the code.

**Version:** 2.0.0  
**Date:** 2024  
**Framework:** NiceGUI (Python Web UI Framework)  
**Status:** Design Specification (partially superseded by `docs/`)

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [NiceGUI Component Specifications](#nicegui-component-specifications)
4. [User Flows](#user-flows)
5. [State Management](#state-management)
6. [API Integration](#api-integration)
7. [UI/UX Specifications](#uiux-specifications)
8. [Implementation Details](#implementation-details)
9. [File Structure](#file-structure)
10. [Edge Cases & Error Handling](#edge-cases--error-handling)

---

## Overview

### Purpose

The NiceGUI-based frontend provides a modern web interface for RescueBox Desktop built entirely in Python. This eliminates the need for Electron, React, or TypeScript, allowing for a unified Python codebase that integrates seamlessly with the FastAPI backend.


---

## Architecture

### High-Level Architecture
┌─────────────────────────────────────────────────────────────┐
│ NiceGUI Application │
│ (Python Server) │
│ │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ NiceGUI UI Components │ │
│ │ ┌────────────┐ ┌────────────┐ ┌──────────────┐ │ │
│ │ │ Pages │ │ Components │ │ State │ │ │
│ │ │ (Routing) │ │ (Reusable) │ │ Management │ │ │
│ │ └────────────┘ └────────────┘ └──────────────┘ │ │
│ └──────────────────────────────────────────────────────┘ │
│ │ │
│ │ HTTP Client │
│ ↓ │
└─────────────────────────────────────────────────────────────┘
│
↓
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Backend (rb-api) + Typer plugin routes │
│ │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ • Models / servers aggregation (`/api/models`, …) │ │
│ │ • Per-plugin POST/GET (e.g. `/audio/transcribe`, …) │ │
│ │ • Chatbot uses Ollama separately for Granite LLM │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────



### Application Structure
n
from nicegui import ui, app
import httpx

# Main application entry point
@ui.page('/')
async def index():
    # Main dashboard page
    pass

@ui.page('/models')
async def models_page():
    # Models listing page
    pass

@ui.page('/chatbot')
async def chatbot_page():
    # Chatbot interface page
    pass

# Run NiceGUI app
ui.run(
    title='RescueBox Desktop',
    port=8080,
    host='127.0.0.1',
    show=False  # Don't auto-open browser
)---

## NiceGUI Component Specifications

### 1. Main Application Layout

**File**: `frontend/main.py`

**Purpose**: Application entry point and routing

from nicegui import ui, app
from nicegui.events import ValueChangeEventArguments
import asyncio
from typing import Optional
import httpx

# Configure NiceGUI
ui.run(
    title='RescueBox Desktop',
    port=8080,
    dark=False,
    favicon='🚑',  # RescueBox icon
    show=False
)

# Shared state
state = {
    'current_user': None,
    'conversations': {},
    'jobs': {},
    'models': []
}

# Navigation bar component
def create_navbar():
    with ui.header().classes('rb-brand-nav text-white shadow-lg'):
        ui.label('🚑 RescueBox Desktop').classes('text-2xl font-bold')
        
        with ui.row().classes('gap-4 ml-auto'):
            ui.link('Models', '/models').classes('text-white hover:underline')
            ui.link('Jobs', '/jobs').classes('text-white hover:underline')
            ui.link('Assistant', '/chatbot').classes('text-white hover:underline')
            ui.link('Logs', '/logs').classes('text-white hover:underline')

# Main layout wrapper
@ui.page('/')
async def index():
    create_navbar()
    
    with ui.column().classes('container mx-auto p-8'):
        ui.label('Welcome to RescueBox Desktop').classes('text-4xl font-bold mb-4')
        ui.label('Select a model or use the Assistant to get started').classes('text-xl text-zinc-600')
        
        with ui.row().classes('gap-4 mt-8'):
            ui.button('Browse Models', on_click=lambda: ui.open('/models')).classes('rb-brand-primary text-white px-6 py-3 rounded-xl')
            ui.button('Open Assistant', on_click=lambda: ui.open('/chatbot')).classes('rb-brand-primary text-white px-6 py-3 rounded-xl')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()

### 2. Chatbot Interface Page

**File**: `frontend/pages/chatbot/chatbot.py` (Main orchestrator)

**Purpose**: Main chatbot interface with conversation history, chat persistence, and **multiple tool call support**

**Key Features:**
- Natural language processing via Granite model for tool selection
- **Multiple tool call handling**: Sequential execution of multiple tool calls with automatic output chaining
- Form-based tool parameter input
- Job submission and result display
- Conversation history persistence

**Features**:
- Natural language query processing
- Tool call generation and form display
- Job submission and results display
- **Chat history persistence** (all messages saved automatically)
- **Tool call re-run** from history
- Conversation management

The chatbot page has been refactored (May 2026) into a modern, package-based architecture to resolve monolithic scaling issues:

- **`frontend/pages/chatbot/`**: New package structure replacing the monolithic orchestrator.
- **`state.py`**: Centralized `ChatbotStateManager` and `ChatMessage` models.
- **`coordinator.py`**: Core orchestration layer including `MessageFlowCoordinator`, `MessageProcessor`, and `ResultProcessor`.
- **`ui.py`**: Main page layout, message rendering, and routing (`/chatbot`).
- **`handlers.py`**: Specialized event handlers, job orchestration, and database services.

See the [Chatbot Architecture Guide](docs/chatbot-architecture.md) for a detailed technical breakdown.



### 3. Models Listing Page

**File**: `frontend/pages/models/models.py`

**Purpose**: Display available models in card-based rows


### 4. Jobs Page

**File**: `frontend/pages/jobs/jobs.py`

**Purpose**: Display job history and status



## State Management

### Reactive State with NiceGUI

The frontend uses NiceGUI's reactive state management with `ui.ref` for UI updates. Each page component manages its own local state:

```python
from nicegui import ui

# Create reactive variables
model_list = ui.ref([])
selected_model = ui.ref(None)
job_status = ui.ref({})

# Use in components
def render_models():
    for model in model_list.value:
        # Render model card
        pass

# Update reactively
model_list.value = await fetch_models()
```

### NiceGUI Storage Integration

The frontend integrates NiceGUI's built-in storage system for session and user-specific state. This provides seamless user experience while maintaining data persistence in SQLite.

**Storage Architecture:**

The application uses a **hybrid storage approach** combining NiceGUI's built-in storage with SQLite:

| Storage Type | Use Case | Persistence | Scope |
|-------------|----------|-------------|-------|
| **`app.storage.user`** | User preferences, conversation state | Cross-session (per browser) | Per-user session |
| **`app.storage.client`** | Draft messages, form state | Temporary (cleared on cache clear) | Per-browser tab |
| **SQLite Database** | Conversations, messages, jobs | Permanent (all sessions) | All users |

**Storage Types:**

1. **`app.storage.user`** - User-specific storage (persists across sessions, tied to NiceGUI user ID):
   - Current conversation_id (restored on page reload)
   - User preferences (dark mode, UI settings, auto-scroll)
   - User-specific UI customizations

2. **`app.storage.client`** - Client-side storage (browser-specific, cleared when cache cleared):
   - Draft messages (as user types)
   - Form draft data (partially filled forms)
   - UI scroll positions

3. **SQLite Database** - Persistent storage (permanent, cross-session):
   - All conversations and messages
   - Job records and execution history
   - Tool call history for re-running

**Utilities:**
- `frontend.utils.nicegui_storage`: Conversation ID and draft management
- `frontend.utils.user_preferences`: User preference management

**Usage Example:**
```python
from frontend.utils.nicegui_storage import (
    get_user_id,
    get_current_conversation_id,
    set_current_conversation_id,
    get_draft_message,
    set_draft_message
)
from frontend.utils.user_preferences import get_user_preferences, set_user_preference

# Get NiceGUI user ID (unique per browser session)
user_id = get_user_id()

# Manage conversation state (persists across page reloads)
conv_id = get_current_conversation_id()
set_current_conversation_id(new_conv_id)

# Save/restore draft messages
draft = get_draft_message()
set_draft_message("partially typed message...")

# Get and set user preferences
prefs = get_user_preferences()
if prefs['auto_scroll']:
    # Enable auto-scroll behavior
    pass

set_user_preference('dark_mode', True)
```

**User Scenarios:**

1. **Conversation Persistence Across Page Reloads:**
   ```python
   # User scenario:
   # 1. User starts a conversation in chatbot
   # 2. User refreshes the page or navigates away and returns
   # 3. Conversation ID is automatically restored from NiceGUI storage
   # 4. User can continue the conversation seamlessly
   ```

2. **Draft Message Preservation:**
   ```python
   # User scenario:
   # 1. User types a long message but accidentally closes the tab
   # 2. User reopens the chatbot page
   # 3. Draft message is automatically restored from client storage
   # 4. User can continue typing without losing work
   ```

3. **User Preferences Persistence:**
   ```python
   # User scenario:
   # 1. User enables dark mode in settings
   # 2. User closes browser and returns later
   # 3. Dark mode preference is automatically restored
   # 4. UI appears in dark mode without user re-configuring
   ```

4. **Form Draft Recovery:**
   ```python
   # User scenario:
   # 1. User fills out a complex form with multiple fields
   # 2. User accidentally navigates away before submitting
   # 3. User returns to the chatbot/form
   # 4. Form data is restored from client storage
   # 5. User can complete and submit without re-entering data
   ```

5. **Cross-Device Limitations (No Login):**
   ```python
   # User scenario (limitation):
   # 1. User configures preferences on Device A
   # 2. User opens application on Device B
   # 3. Preferences are NOT shared (different NiceGUI user IDs)
   # 4. User must reconfigure preferences on each device
   ```

**Limitations (No User Login):**

Since there is **no user authentication/login system**, NiceGUI storage has the following limitations:

1. **Per-Browser Storage**: Each browser/browser profile gets a unique NiceGUI user ID. Different browsers on the same machine are treated as different users.

2. **No Cross-Device Sync**: Preferences and conversation state stored in NiceGUI storage are **NOT synchronized** across devices. Each device has its own user ID.

3. **Browser-Cache Dependent**: `app.storage.client` data (drafts, form state) is lost if the user clears browser cache/cookies.

4. **No User Identity**: There's no way to identify a "real user" across different browsers or devices. NiceGUI user IDs are session-based, not account-based.

5. **Data Isolation**: Conversations and jobs in SQLite are shared across all sessions on the same machine, but each browser session has separate NiceGUI storage.

**Best Practices:**

1. **Use SQLite for Permanent Data**: All conversations, messages, and jobs are stored in SQLite, ensuring they persist regardless of browser cache clearing.

2. **Use NiceGUI Storage for UX**: Use `app.storage.user` for preferences and session state that enhance user experience but aren't critical if lost.

3. **Use Client Storage Sparingly**: Only use `app.storage.client` for temporary drafts that can be recreated if lost.

4. **Future Enhancement**: If multi-device sync is needed, implement user authentication and link NiceGUI user IDs to real user accounts.

**Hybrid Approach Benefits:**
- **SQLite**: Ensures all important data (conversations, jobs) is permanently stored
- **NiceGUI Storage**: Provides seamless UX (preferences, drafts) without requiring authentication
- **Combination**: Best of both worlds - data persistence + user convenience

Session storage vs SQLite: see `docs/database.md`.

**Note**: State is managed locally within each page component. NiceGUI storage complements local state by providing session persistence and user-specific preferences without requiring a login system.

### UI Workflows

The frontend implements three major UI workflows for different user interaction patterns:

- **Assistant / chat (`/chatbot`)**: Natural language processing with Granite (Ollama) tool selection and plugin job execution
- **Models (`/models`)**: Manual tool browsing and selection
- **History**: Conversation restoration, load, and re-run (`?load_conversation=`, `?rerun=`)

Canonical documentation lives under **`docs/README.md`** (workflow, theme, chat history, jobs, DB, results, pipeline/filter, testing).

## API Integration

### Backend API Endpoints

The frontend communicates with the FastAPI backend through standardized REST endpoints. The backend provides aggregation endpoints that simplify plugin discovery and management.

#### Model Management Endpoints

The backend (`src/rb-api/rb/api/routes/models.py`) provides unified endpoints for model/plugin discovery. The frontend **`ApiClient`** uses **`API_BASE_URL`** (default includes **`/api`**), so calls are typically **`GET /api/models`**, **`GET /api/servers`**, etc.

- **`GET /api/models`** (via client) — Returns list of all available plugins as models
  ```json
  [
    {
      "uid": "audio_transcription",
      "name": "Audio transcription library",
      "plugin_name": "audio_transcription",
      "version": "3.0.0",
      "author": "Rescue Lab",
      "info": "Markdown documentation...",
      "gpu": false
    }
  ]
  ```

- **`GET /api/models/{model_uid}`** — Returns metadata for a specific plugin
- **`GET /api/models/{model_uid}/info`** — Alternative endpoint for model metadata (alias)

#### Server Status Endpoints

- **`GET /api/servers`** — Returns list of all registered servers
  ```json
  [
    {
      "modelUid": "audio_transcription",
      "serverAddress": "localhost",
      "serverPort": 8000,
      "isUserConnected": true,
      "pluginName": "audio_transcription"
    }
  ]
  ```
  All plugins are served by the same backend server (localhost:8000), so each plugin gets one server entry.

- **`GET /api/servers/{model_uid}/status`** — Returns server status for a specific model
  ```json
  {
    "status": "Online",
    "modelUid": "audio_transcription",
    "serverAddress": "localhost",
    "serverPort": 8000
  }
  ```
  All registered plugins return "Online" status by default since they're all served by the current backend.

#### Backend Implementation

The backend aggregation layer (`src/rb-api/rb/api/routes/models.py`) works by:

1. **Plugin Discovery**: Iterates through `rescuebox_app.registered_groups` to find all registered plugins
2. **Metadata Fetching**: For each plugin, finds and calls the `app_metadata` command using `static_endpoint()`
3. **Data Transformation**: Converts plugin metadata to frontend-expected format with `uid`, `name`, `version`, etc.
4. **Server Information**: Returns server details (localhost:8000) for all plugins since they share the same backend

This approach provides a clean abstraction layer that:
- ✅ Simplifies frontend code (single endpoint per resource)
- ✅ Matches REST API best practices
- ✅ Allows backend optimization/caching in the future
- ✅ Provides consistent data format across all plugins

For API usage from the UI, see `docs/workflow.md` and `src/rb-api/`.

### Local Database Storage

The frontend includes a SQLite database module (`frontend/database/job_db.py`) for persistent job storage, similar to the Electron app's database functionality.

#### JobDB Module

The `JobDB` class provides CRUD operations for jobs:

- **Location**: `frontend/database/job_db.py`
- **Database File**: `frontend/data/jobs.db` (created automatically)
- **Schema**: Stores job `uid`, `modelUid`, `taskUid`, `endpoint`, timestamps, status, request/response JSON, and task schema

#### Key Features

- **Job Storage**: All submitted jobs are saved to the local database
- **Job History**: Jobs can be viewed, filtered, and re-submitted from the Jobs page
- **Job Details**: Full job information including inputs, parameters, and results
- **Re-submission**: Jobs can be re-submitted with the same parameters
- **Status Tracking**: Jobs track status (Running, Completed, Failed, Canceled)

#### Usage

```python
from frontend.database import get_job_db

# Get database instance (singleton)
job_db = get_job_db()
job_db.connect()

# Create a job
await job_db.create_job(
    uid=job_uid,
    model_uid=model_uid,  # Optional for chatbot jobs
    task_uid=task_uid,    # Optional for chatbot jobs
    endpoint=endpoint,    # For chatbot jobs
    start_time=start_time,
    status='Running',
    request=request_json,
    task_schema=task_schema_json
)

# Update job status
await job_db.update_job_status(job_uid, 'Completed')
await job_db.update_job_response(job_uid, response_json)

# Get all jobs
jobs = await job_db.get_all_jobs()

# Get specific job
job = await job_db.get_job_by_uid(job_uid)

# Delete job
await job_db.delete_job(job_uid)
```

#### Database Initialization

The database is initialized in `frontend/main.py` on application startup:

```python
from frontend.database import get_job_db

# Initialize database
job_db_instance = get_job_db()
job_db_instance.connect()
```

The database connection is automatically closed on application shutdown.

#### Comparison with Electron App

**Electron (Old)**:
- Models stored in SQLite (`MLModelDb`)
- Tasks stored in SQLite (`TaskDb`)
- Jobs stored in SQLite (`JobDb`)

**NiceGUI (New)**:
- Models: Fetched dynamically from API (`/models`)
- Tasks: Fetched dynamically from API (via plugin endpoints)
- Jobs: Stored locally in SQLite (`JobDB`)

The new architecture simplifies data management by using the API as the source of truth for models and tasks, while maintaining local storage for jobs (which represent user actions and history).

For more details, see `docs/ELECTRON_VS_NICEGUI_COMPARISON.md`.

### Audit Trails

The frontend includes a comprehensive audit trail feature that generates detailed reports of job executions. Audit trails include:

- User chat prompts
- Tool selections and configurations
- Inputs and parameters
- Outputs and results
- Errors and status messages
- Application logs (filtered by job ID, model ID, and time range)

Audit trails can be exported from the job details page as Markdown files. The audit trail generation uses contextual logging to filter logs specific to each job.

**Usage**:
1. Navigate to a job's details page
2. Click the "📋 Export Audit Trail" button
3. A Markdown file will be downloaded with all job information

Audit trail UI: `frontend/pages/jobs/job_audit.py`. Contextual logging: `frontend/utils/logging_context.py`.

### Contextual Logging

The frontend uses a contextual logging system that automatically includes job IDs, model IDs, and session IDs in all log messages. This enables:

- Precise log filtering by job or model
- Automatic log inclusion in audit trails
- Better debugging and traceability

Logs are written to `frontend/data/rescuebox.log` with the format:
```
{timestamp} | {level} | job_id={job_id} | model_id={model_id} | session_id={session_id} | {logger} | {message}
```

The logging context is automatically set when jobs are created, ensuring all subsequent logs include the relevant IDs.

### API Client Usage

Shared **`ApiClient`** (`frontend/api_client.py`) with **`API_BASE_URL`** from `frontend/config.py` (default `http://localhost:<RESCUEBOX_PORT>/api`). Chatbot plugin calls use **`ChatbotConfig.RESCUEBOX_HOST`** and raw paths in `api_helpers.post_job` / `fetch_task_schema`.

## File Structure

### Directory Layout

```
frontend/
├── main.py                      # Application entry point
├── config.py                    # Configuration settings
├── components/                  # Reusable UI components (REFACTORED 2025)
│   ├── __init__.py
│   ├── base_component.py        # Abstract base component class
│   ├── component_utils.py       # Shared component utilities
│   ├── chat/                    # Chat components (2026 Modular Refactor)
│   │   ├── __init__.py          # Public API facade
│   │   ├── rendering.py         # Message & Card renderers
│   │   ├── ui_elements.py       # Header, Window, Input Area
│   │   ├── dialogs.py           # Help, History, View Modals
│   │   └── utils.py             # UIOperations & Styling
│   ├── forms/                   # Form components (2026 Modular Refactor)
│   │   ├── __init__.py          # Public API facade
│   │   ├── form_generator.py    # FormGenerator & Orchestration
│   │   ├── field_builders.py    # Input & Parameter builders
│   │   └── dialogs.py           # Case Notes & UI Modals
│   ├── jobs/                    # Job-specific components
│   ├── models/                  # Model-specific components
│   ├── results/                 # Results display components
│   │   ├── renderers/           # Individual result renderers
│   │   └── ...
│   └── shared/                  # Shared UI components (navbar, notifications, etc.)
├── pages/                       # Page components
│   ├── __init__.py
│   ├── models/                  # Models page components
│   ├── jobs/                    # Jobs package (2026 Modular Refactor)
│   │   ├── __init__.py          # Public API facade
│   │   ├── list.py              # Jobs Listing Page
│   │   ├── details.py           # Job Details Page
│   │   ├── components.py        # Audit Trail & Action buttons
│   │   └── utils.py             # Pipeline & Field helpers
│   ├── chatbot/                 # Chatbot package (2026 Modular Refactor)
│   │   ├── __init__.py          # Public API facade
│   │   ├── state.py             # ChatbotStateManager & Models
│   │   ├── coordinator.py       # Flow coordination & Orchestration
│   │   ├── ui.py                # Main Page & Rendering logic
│   │   └── handlers.py          # Event Handlers & Services
│   └── logs/                    # Logs page
├── chatbot/                     # Legacy chatbot module (being phased out)
│   ├── __init__.py
│   ├── config.py                # Configuration & tool registry
│   ├── core.py                  # Core business logic
│   ├── message_handler.py       # Message routing & handling
│   └── utils.py                 # Utility functions
├── database/                    # Database module (REFACTORED 2024)
│   ├── __init__.py
│   ├── base_db.py               # Abstract base database class
│   ├── schemas.py               # Database schema definitions
│   ├── validation.py            # Data validation & serialization
│   ├── job_db.py                # Job database (refactored)
│   └── chat_history_db.py       # Chat history database
├── utils/                       # Utility package (2026 Modular Refactor)
│   ├── __init__.py              # Public API facade
│   ├── logging.py               # Audit trails & Contextual logging
│   ├── paths.py                 # Path resolution & Backend setup
│   ├── browser.py               # File/Directory browsers
│   ├── validators.py            # Pydantic form/response validation
│   ├── storage.py               # User preferences & Storage
│   └── ui.py                    # Notifications & UI helpers
└── tests/                       # Test suite (ENHANCED 2025)
    ├── conftest.py              # Pytest fixtures
    ├── unit/                    # Unit tests (54 new component tests)
    │   ├── test_base_component.py    # Base component tests
    │   ├── test_form_components.py   # Form component tests
    │   ├── test_shared_components.py # Shared component tests
    │   ├── test_chat_components.py   # Chat component tests
    │   ├── test_components.py        # Results component tests
    │   └── ...                      # 25+ other test files
    └── integration/             # Integration tests
        ├── test_ui_integration.py    # UI workflow tests
        └── ...                      # 10+ integration test files
```

### Enhanced UI Components

#### Notifications

The frontend includes an enhanced notification system with better styling and positioning:

- **Location**: `frontend/components/shared/notifications.py`
- **Functions**: `notify_success()`, `notify_error()`, `notify_info()`, `notify_warning()`
- **Integration**: Automatically used by `frontend/utils/error_handling.py`
- **Benefits**: Consistent styling, configurable positioning, persistent option

#### Workflow Stepper

A visual progress indicator component for multi-step workflows:

- **Location**: `frontend/components/shared/stepper.py`
- **Use Cases**: Chatbot workflow, form submission, multi-step wizards
- **Features**: Visual progress, step navigation, completion tracking
- **Example**: Chatbot workflow (Message → Tool → Form → Submit → Results)

See `docs/STEPPER_AND_NOTIFICATIONS.md` for detailed documentation and examples.

### Component Architecture (2025 Refactoring)

The frontend has been comprehensively refactored into a modern, modular architecture with extensive testing coverage:

#### **Base Component System**
- **`base_component.py`**: Abstract `BaseComponent` class providing standardized patterns
- **`component_utils.py`**: Shared utilities for theming, validation, and common operations
- **Benefits**: Consistent error handling, standardized UI displays, reusable patterns

#### **Specialized Component Categories**

##### **Form Components** (`frontend/components/forms/`)
- **`form_generator.py`**: Main `FormGenerator` orchestrator class
- **`builders/`**: Field builders for inputs (`input_field_builder.py`) and parameters (`parameter_field_builder.py`)
- **`form_generator.py`**: Form submission and validation logic
- **Features**: Dynamic form generation, type-safe field creation, comprehensive validation

##### **Results Components** (`frontend/components/results/`)
- **`results_preview.py`**: Main dispatcher for result rendering
- **`renderers/`**: Specialized renderers for each result type (text, markdown, batch files, etc.)
- **`results_utils.py`**: Platform-specific file/folder operations
- **`table_helpers.py`**: Table rendering utilities for batch results
- **Features**: Type-specific rendering, expandable previews, file operations

##### **Shared Components** (`frontend/components/shared/`)
- **`notifications.py`**: Enhanced notification system with theming
- **`navbar.py`**: Navigation bar component
- **`breadcrumbs.py`**: Breadcrumb navigation
- **`stepper.py`**: Visual progress indicators
- **Features**: Consistent styling, responsive design, accessibility

##### **Chat Components** (`frontend/components/chat/`)
- **`rendering.py`**: Welcome and message/list cards  
- **`dialogs.py`**, **`view.py`**: History, conversation view, load/rerun helpers  
- **`utils.py`, `ui_elements.py`**, **`ui_bridge.py`**: Composer area, scrolling helpers (test patches)

#### **Page-Level Architecture** (`frontend/pages/`)

##### **Chatbot Page** (Heavily Refactored - 20+ modules)
- **`chatbot.py`**: Main orchestrator class
- **`chatbot_handlers.py`**: Message routing, form submission wrapper, etc.
- **`utils/`**: Utility classes - `JobSubmissionOrchestrator`, `ResultProcessor`, etc.
- **`state/`**: State management classes (`ChatbotStateManager`)
- **`parameter_handlers.py`**: URL parameter processing
- **`constants.py`**: Configuration constants

##### **Database Architecture** (Refactored 2024)
- **`base_db.py`**: Abstract base class with common database operations
- **`schemas.py`**: Schema definitions using Strategy pattern
- **`validation.py`**: Data validation and serialization utilities
- **`job_db.py`**: Job persistence (refactored to use base classes)
- **`chat_history_db.py`**: Chat history persistence
- **Features**: Connection pooling, transaction management, schema validation

### Benefits of Modular Architecture

- **Smaller Files**: Large files split into focused, manageable modules
- **Better Organization**: Clear separation of concerns
- **Easier Maintenance**: Changes to specific functionality isolated
- **Backward Compatible**: Public APIs remain unchanged
- **Testability**: Each module can be tested independently

### Usage Examples

#### Form Generation

```python
from frontend.components.forms import FormGenerator

generator = FormGenerator()
await generator.generate_form(
    schema=task_schema,
    container=ui.column(),
    initial_values={'inputs': {...}, 'parameters': {...}},
    onSubmit=handle_submit
)
```

#### Results Preview

```python
from frontend.components.results import ResultsPreview

ResultsPreview.render(container, response_body)
```

#### Chatbot Page

```python
from frontend.pages.chatbot import ChatbotPage

# Main usage (unchanged API)
chatbot = ChatbotPage()
chatbot.render()

# Or use the page route directly
from frontend.pages.chatbot import chatbot_page
# Automatically registered as @ui.page('/chatbot')
```

All APIs remain unchanged despite the internal refactoring.

### Unit test patch paths

After splitting monolithic modules, tests often patch these import paths:

- `frontend.components.results` — re-exports `os`, `ui`, `subprocess`, `platform` for renderer tests
- `frontend.components.shared.notifications` (and `navbar`, `stepper`, `breadcrumbs`) — legacy aliases on the shared package
- `frontend.components.forms.form_generator` — form submission (alias `form_handlers` kept for compatibility)
- `frontend.pages.chatbot.ui_flow` — `load_and_show_form`, `show_results`
- `frontend.pages.chatbot.handlers.pipeline` — pipeline step handlers

## Code Quality & Documentation

### Documentation

All modules, classes, and methods include comprehensive docstrings following the NumPy docstring style:

- **Module-level docstrings**: Describe the module's purpose and key components
- **Class docstrings**: Explain class responsibilities and usage
- **Method/function docstrings**: Include:
  - Brief description
  - Detailed explanation
  - Args section with parameter descriptions
  - Returns section
  - Raises section (when applicable)
  - Examples section (when helpful)
  - Tips section for developers

Example:

```python
def my_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Brief one-line description.
    
    Longer description explaining what the function does, when to use it,
    and any important context.
    
    Args:
        param1 (str): Description of parameter
        param2 (int): Description with default value. Defaults to 10.
    
    Returns:
        Dict[str, Any]: Description of return value structure
    
    Raises:
        ValueError: When parameter is invalid
    
    Examples:
        >>> result = my_function("test", 20)
        >>> result['key']  # Access result
    
    Tips:
    - Useful tip for developers
    - Another helpful note
    """
```

For logging behavior, see `frontend/main.py` and `frontend/utils/logging_context.py`.

## Development Guidelines

### Adding New Components

1. Create the component file in `frontend/components/`
2. Add comprehensive docstrings and logging
3. Export from `frontend/components/__init__.py`
4. Write tests in `frontend/tests/unit/test_components.py`

### Refactoring Guidelines

When files grow large (>400 lines), consider splitting them:

1. **Identify logical boundaries**: Separate concerns (UI, business logic, utilities)
2. **Maintain backward compatibility**: Keep public APIs unchanged
3. **Create focused modules**: Each module should have a single responsibility
4. **Update imports**: Ensure all imports are updated
5. **Test thoroughly**: Verify existing tests still pass
6. **Update documentation**: Update README and docstrings

#### Recent Refactoring Examples

**Form Generator** (569 → 184 + 257 + 179 lines):
- Split UI orchestration, field building, and form handling

**Results Preview** (467 → 147 + 313 + 90 lines):
- Split dispatcher, individual renderers, and utility functions

**Chatbot Page** (600 → 311 + 179 + 120 + 99 + 215 lines):
- Split main orchestrator, message/form handlers, message components, UI layout, and form handlers
- Reduced main file by ~48% (from 600 to 311 lines) while improving maintainability
- Extracted complex message processing and form submission logic into dedicated handler module

### Testing (Enhanced 2025)

Comprehensive test suite with 54 new component tests and extensive coverage:

#### **Test Categories**
- **Unit Tests**: Individual component and utility testing (54 component tests added)
- **Integration Tests**: UI workflow testing using NiceGUI's testing framework
- **Database Tests**: SQLite database operations and schema validation
- **API Tests**: Backend integration and endpoint testing

#### **Component Test Coverage**
```
✅ Base Components (6 tests) - BaseComponent, ComponentRegistry, ComponentUtils
✅ Form Components (11 tests) - FormGenerator, builders, handlers
✅ Shared Components (13 tests) - Notifications, navbar, breadcrumbs, stepper
✅ Chat Components (10 tests) - Conversation actions, rendering, panels
✅ Results Components (14 tests) - Various result type renderers
```

#### **Running Tests**

```bash
# Run all tests
poetry run pytest frontend/tests/

# Run only unit tests
poetry run pytest frontend/tests/unit/

# Run component tests specifically
poetry run pytest frontend/tests/unit/test_*component*.py

# Run with coverage
poetry run pytest frontend/tests/ --cov=frontend --cov-report=html

# Run specific component test
poetry run pytest frontend/tests/unit/test_base_component.py -v

# Run integration tests (UI workflows)
poetry run pytest frontend/tests/integration/test_ui_integration.py
```

#### **Test Architecture**
- **Mocking Strategy**: Proper isolation of UI components and external dependencies
- **Fixture Management**: Reusable test fixtures in `conftest.py`
- **Assertion Patterns**: Comprehensive assertions for component behavior
- **CI/CD Integration**: All tests designed to run in automated environments

See **`docs/testing.md`**, **`frontend/tests/pytest.ini`**, and **`frontend/tests/integration/README.md`**.
