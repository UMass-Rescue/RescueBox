# Backend API Mismatch Analysis

## Problem

The NiceGUI frontend expects certain API endpoints that **do not exist** in the previous electron implementation.

## Frontend Expectations

The frontend code (`frontend/pages/models.py`, `frontend/pages/jobs.py`, etc.) expects:

1. **`GET /models`** - Returns a list of all available models/plugins
2. **`GET /models/{model_uid}`** - Returns metadata for a specific model
3. **`GET /models/{model_uid}/info`** - Alternative endpoint for model metadata
4. **`GET /servers`** - Returns a list of all registered servers
5. **`GET /servers/{model_uid}/status`** - Returns server status for a model

## Backend Reality

The backend (`src/rb-api/rb/api/routes/cli.py`) dynamically creates routes from Typer CLI commands. It provides:

1. **Individual plugin endpoints:**
   - `/{plugin_name}/api/app_metadata` - Returns `AppMetadata` for a plugin (GET)
   - `/{plugin_name}/api/routes` - Returns list of routes/endpoints for a plugin (GET)
   - `/{plugin_name}/{endpoint}/task_schema` - Returns task schema for an endpoint (GET)

2. **No aggregation endpoints:**
   - There is **NO** `/models` endpoint that aggregates all plugins
   - There is **NO** `/servers` endpoint
   - There is **NO** model-by-UID lookup endpoint

## Example Backend Endpoints

For a plugin named `audio_transcription`, the backend provides:
- `GET /audio_transcription/api/app_metadata` → Returns `AppMetadata` object
- `GET /audio_transcription/api/routes` → Returns list of `SchemaAPIRoute` objects
- `GET /audio_transcription/{endpoint}/task_schema` → Returns `TaskSchema` object

## Solution

### Create Backend Aggregation Endpoints (Recommended)

Add new routes to `src/rb-api/rb/api/routes/` to aggregate plugin information:

```python
# src/rb-api/rb/api/routes/models.py
@router.get("/models")
async def get_models():
    """Aggregate all plugins and return as models list"""
    # Iterate through rescuebox_app.registered_groups
    # Call each plugin's /api/app_metadata endpoint
    # Return unified list

@router.get("/models/{model_uid}")
async def get_model_by_uid(model_uid: str):
    """Get model metadata by plugin name (model_uid)"""
    # Call {model_uid}/api/app_metadata
```


## Current Impact

**The frontend will fail with 404 errors** when trying to:
- Load the models page (`/models`)
- Get model details (`/models/{model_uid}/details`)
- Check server statuses (`/servers`)
- Display model information in job details

## Electron vs NiceGUI Architecture

**Electron (Old):**
- Models stored in local SQLite database (`MLModelDb`)
- Servers stored in local SQLite database (`ModelServerDb`)
- Models registered manually via IPC handlers
- No API endpoints needed

**NiceGUI (New):**
- Models should be discovered from backend API
- No local model database (API is source of truth)
- Need aggregation endpoints to provide unified model view
- Server status tracking needs implementation

## Recommendation

**Implement Option 1** - Create backend aggregation endpoints because:
1. Cleaner separation of concerns
2. Consistent with REST API design
3. Easier for frontend to consume
4. Can add caching/optimization in backend
5. Matches frontend expectations

## Next Steps

1. Create `src/rb-api/rb/api/routes/models.py` with aggregation endpoints
2. Register routes in `src/rb-api/rb/api/routes/__init__.py`
3. Include router in `src/rb-api/rb/api/main.py`
4. Update frontend if response format differs
5. Consider server status tracking if needed

