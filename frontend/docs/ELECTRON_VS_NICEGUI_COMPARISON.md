# Electron vs NiceGUI: Models and Tasks Comparison

## Overview

This document compares how Models and Tasks are handled in the old Electron codebase versus the new NiceGUI implementation.

## Electron Codebase Architecture

### Models (MLModelDb)
- **Storage**: SQLite database (`mlmodels` table)
- **Purpose**: Store registered ML model service metadata
- **Fields**:
  - `uid`: Unique identifier (MD5 hash of routes)
  - `name`, `version`, `author`, `info`: Metadata
  - `gpu`: GPU requirement flag
  - `routes`: JSON of API routes (APIRoutes)
  - `isRemoved`: Soft-delete flag
  - `updatedAt`: Last update timestamp

- **Functionality**:
  - Models are registered when a service connects
  - Can be soft-deleted (`isRemoved = true`) but not hard-deleted
  - Models persist between sessions
  - Used to list available models and check their status

### Tasks (TaskDb)
- **Storage**: SQLite database (`tasks` table)
- **Purpose**: Store individual endpoints/capabilities of each model
- **Fields**:
  - `id`: Auto-increment primary key
  - `taskId`: Task identifier (string)
  - `modelUid`: Foreign key to MLModelDb
  - `shortTitle`: Display name for the task
  - `taskRoute`: API route path
  - `taskOrder`: Display order

- **Functionality**:
  - Tasks are created when a model is registered (one per endpoint)
  - Tasks belong to a model (many-to-one relationship)
  - Used to:
    - List available tasks for a model
    - Get task metadata (shortTitle) for notifications
    - Map taskId to API routes
  - **Note**: `taskSchema` was originally in tasks table but moved to jobs table (migration 0010)

### Jobs (JobDb)
- **Storage**: SQLite database (`jobs` table)
- **Links**: Both `modelUid` and `taskUid` (required)
- **Stores**: `taskSchema` at time of execution (snapshot)
- **Purpose**: Track job execution history

## NiceGUI Codebase Architecture

### Models
- **Storage**: **NOT stored locally** - fetched dynamically from API
- **API Endpoints**: 
  - `/models` - List all models
  - `/models/{model_uid}` - Get model details
  - `/models/{model_uid}/info` - Get model metadata
- **Functionality**:
  - Models are fetched on-demand from the FastAPI backend
  - Server status is checked dynamically (`/servers/{model_uid}/status`)
  - Display model metadata and status in UI
  - Link to model details and run pages

### Tasks
- **Storage**: **NOT stored separately** - fetched on-demand from API
- **API Endpoints**:
  - `/models/{model_uid}/tasks` - List tasks for a model
  - `/models/{model_uid}/tasks/{task_uid}/schema` - Get task schema
  - For chatbot: Task schemas fetched directly via endpoint paths (e.g., `/audio/transcribe/task_schema`)

- **Functionality**:
  - Task schemas are fetched when needed (form generation, job submission)
  - No local storage of task metadata
  - Chatbot workflow uses endpoint names directly (e.g., "audio/transcribe")

### Jobs (JobDB)
- **Storage**: SQLite database (`jobs` table) - **LOCAL STORAGE**
- **Links**: Supports **both**:
  - Traditional: `modelUid` + `taskUid`
  - Chatbot: `endpoint` (e.g., "audio/transcribe")
- **Stores**: `taskSchema` at time of execution (snapshot)
- **Purpose**: Track all job execution history (both traditional and chatbot jobs)

## Key Differences

### 1. Model Storage
| Aspect | Electron | NiceGUI |
|--------|----------|---------|
| Storage | SQLite (persistent) | API (dynamic) |
| Offline Access | Yes | No |
| Registration | Stored when service connects | Always fetched from API |
| Status Check | From database | Real-time API check |

### 2. Task Storage
| Aspect | Electron | NiceGUI |
|--------|----------|---------|
| Storage | SQLite (persistent) | API (on-demand) |
| Metadata | Stored (shortTitle, taskRoute, taskOrder) | Fetched when needed |
| Listing | From database | From API |
| Purpose | Historical record + fast access | Current state only |

### 3. Job Storage
| Aspect | Electron | NiceGUI |
|--------|----------|---------|
| Storage | SQLite | SQLite |
| Model/Task Link | Required (modelUid + taskUid) | Flexible (modelUid/taskUid OR endpoint) |
| Task Schema | Stored in job (snapshot) | Stored in job (snapshot) |
| History | Full history | Full history |

## Functionality Comparison

### What Electron Had:
1. ✅ **Offline Model Access**: Could view registered models without API
2. ✅ **Task Metadata Storage**: shortTitle stored for notifications
3. ✅ **Historical Task List**: See what tasks existed even if model offline
4. ✅ **Model Registration Tracking**: Persistent record of registered models

### What NiceGUI Has:
1. ✅ **Real-time Model Status**: Always current, no stale data
2. ✅ **Simpler Architecture**: No sync between local DB and API
3. ✅ **Chatbot Integration**: Direct endpoint usage (bypasses model/task concept)
4. ✅ **Job History**: Full history stored locally (including taskSchema snapshots)
5. ✅ **Dynamic Task Schemas**: Always get latest schema from API

### What's Missing in NiceGUI:
1. ❌ **Offline Model Access**: Requires API connection
2. ❌ **Task Metadata Caching**: shortTitle fetched on-demand (if needed)
3. ❌ **Model Registration Tracking**: No local record of registered models

## Do We Need Models and Tasks Storage?

### Recommendation: **NO** - Current approach is sufficient

**Reasons:**

1. **Models are Dynamic**
   - Models represent running services that can start/stop
   - Storing them locally creates sync issues (stale data)
   - Real-time status checking is more accurate

2. **Tasks are Ephemeral**
   - Task schemas change with API versions
   - Jobs already store taskSchema snapshots (historical context preserved)
   - On-demand fetching ensures latest schema

3. **Chatbot Workflow Benefits**
   - Direct endpoint usage is simpler
   - No need to resolve modelUid/taskUid
   - More flexible for new workflows

4. **Jobs Provide Historical Context**
   - taskSchema stored in jobs gives historical record
   - Can reconstruct what tasks existed by examining jobs
   - No separate task storage needed for history

5. **Simpler Maintenance**
   - No database synchronization logic needed
   - No cleanup of orphaned models/tasks
   - Fewer moving parts = less bugs

### When You WOULD Need Local Storage:

1. **Offline Mode**: If you need to view models/tasks without API connection
2. **Performance**: If API calls are too slow (not currently an issue)
3. **Notifications**: If you need shortTitle for notifications (currently not implemented)

## Current Implementation Status

### ✅ Fully Functional:
- Model listing and details (from API)
- Task schema fetching (from API)
- Job history (local SQLite)
- Chatbot workflow (direct endpoints)
- Traditional workflow (modelUid/taskUid)

### 🔄 Could Be Enhanced (but not critical):
- Task metadata caching for notifications
- Offline model list (if needed)
- Model registration tracking (if needed)

## Conclusion

The NiceGUI implementation **does not need** separate Models and Tasks database tables. The current approach is:

- **Simpler**: Less code to maintain
- **More Flexible**: Supports both traditional and chatbot workflows
- **More Accurate**: Real-time data from API
- **Sufficient**: Jobs table provides historical context

The only functionality "lost" is:
- Offline model/task access (not critical for web UI)
- Task metadata caching (can be added if needed for performance)

**Recommendation**: Keep the current implementation. It's cleaner and provides all necessary functionality.

