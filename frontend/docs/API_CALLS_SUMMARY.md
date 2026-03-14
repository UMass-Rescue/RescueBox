# Frontend API Calls to Backend - Complete List

This document lists all HTTP API calls made from the NiceGUI frontend to the RescueBox FastAPI backend.

## Summary by Endpoint

### Model Management Endpoints

#### `GET /models`
- **Purpose**: Fetch list of all available plugins/models
- **Location**: 
  - `frontend/pages/models.py:111` - `load_models()` method
- **Usage**: Models listing page

#### `GET /models/{model_uid}`
- **Purpose**: Get metadata for a specific model/plugin
- **Location**:
  - `frontend/pages/jobs.py:175` - `get_plugin_name()` method
  - `frontend/pages/job_details.py:251` - `render_job_details()` function
- **Usage**: Display model names in job listings and details

#### `GET /models/{model_uid}/info`
- **Purpose**: Alternative endpoint for model metadata (alias)
- **Location**:
  - `frontend/pages/model_details.py:49` - `model_details_page()` function
- **Usage**: Model details page (falls back to `/models/{model_uid}` if this fails)

#### `GET /servers`
- **Purpose**: Get list of all registered servers
- **Location**:
  - `frontend/pages/models.py:121` - `load_models()` method
- **Usage**: Models listing page to get server information

#### `GET /servers/{model_uid}/status`
- **Purpose**: Get server status for a specific model
- **Location**:
  - `frontend/pages/models.py:132` - `load_models()` method (checks status for each model)
  - `frontend/pages/model_details.py:71` - `model_details_page()` function
- **Usage**: Display server status (Online/Offline) in models page and model details

### Chatbot/Agent Endpoints

#### `POST /agent/chat`
- **Purpose**: Send chat message to agent for tool selection
- **Location**:
  - `frontend/chatbot/core.py` - (via ChatbotCore, but not directly - handled by message_handler)
  - Note: This endpoint is called internally by the message handler system
- **Usage**: Chatbot message processing

### Task Schema Endpoints

#### `GET /{endpoint}/task_schema`
- **Purpose**: Fetch task schema for a specific endpoint
- **Location**:
  - `frontend/chatbot/core.py:123` - `get_task_schema_from_endpoint()` method
- **Usage**: Chatbot form generation
- **Example**: `GET /audio/transcribe/task_schema`
- **Note**: Endpoint path is normalized (leading slash added if missing)

### Job Execution Endpoints

#### `POST /{endpoint}`
- **Purpose**: Submit job to execute a task
- **Location**:
  - `frontend/chatbot/core.py:301` - `submit_job()` method
- **Usage**: Submit jobs after form completion
- **Example**: `POST /audio/transcribe` with JSON body containing inputs and parameters
- **Note**: Endpoint path is normalized (leading slash added if missing)

### Ollama/Granite Model Endpoints (External)

#### `POST /api/generate` (Ollama)
- **Purpose**: Call Granite model for tool selection
- **Location**:
  - `frontend/chatbot/core.py:357` - `call_granite_model()` method
- **Base URL**: Configured via `ChatbotConfig.OLLAMA_HOST` (default: `http://localhost:11434`)
- **Usage**: Natural language to tool call conversion

---

## Detailed Breakdown by File

### `frontend/pages/models.py`

```python
# GET /models - Line 111
models_response = await self.api_client.get('/models')

# GET /servers - Line 121
servers_response = await self.api_client.get('/servers')

# GET /servers/{model_uid}/status - Line 132 (in loop)
status_response = await self.api_client.get(f'/servers/{model_uid}/status')
```

**Context**: Models listing page - loads all models, servers, and checks status

### `frontend/pages/jobs.py`

```python
# GET /models/{model_uid} - Line 175
response = await self.api_client.get(f'/models/{model_uid}')
```

**Context**: Job listing page - fetches model name for display in job rows

### `frontend/pages/job_details.py`

```python
# GET /models/{model_uid} - Line 251
model_response = await api_client.get(f'/models/{model_uid}')
```

**Context**: Job details page - fetches model information for display

### `frontend/pages/model_details.py`

```python
# GET /models/{model_uid}/info - Line 49 (primary)
model_response = await api_client.get(f'/models/{model_uid}/info')

# GET /models/{model_uid} - Line 53 (fallback)
model_response = await api_client.get(f'/models/{model_uid}')

# GET /servers/{model_uid}/status - Line 71
status_response = await api_client.get(f'/servers/{model_uid}/status', timeout=5.0)
```

**Context**: Model details page - displays model metadata and server status

### `frontend/chatbot/core.py`

```python
# GET /{endpoint}/task_schema - Line 123
schema_response = await self.api_client.get(schema_endpoint)
# Where schema_endpoint = f'/{endpoint}/task_schema'

# POST /{endpoint} - Line 301
job_response = await self.api_client.post(api_endpoint, json=request_dict)
# Where api_endpoint = f'/{endpoint}'

# POST /api/generate (Ollama) - Line 357
response = await self.ollama_client.post(
    "/api/generate",
    json={
        "model": self.config.GRANITE_MODEL,
        "prompt": prompt,
        "stream": False
    }
)
```

**Context**: Core chatbot logic - fetches task schemas, submits jobs, calls Granite model

---

## API Client Instances

### Direct `httpx.AsyncClient` Usage

The following files create their own `httpx.AsyncClient` instances:

1. **`frontend/pages/models.py`** - `self.api_client = httpx.AsyncClient(base_url='http://localhost:8000')`
2. **`frontend/pages/jobs.py`** - `self.api_client = httpx.AsyncClient(base_url='http://localhost:8000')`
3. **`frontend/pages/job_details.py`** - `api_client = httpx.AsyncClient(base_url='http://localhost:8000')`
4. **`frontend/pages/model_details.py`** - `api_client = httpx.AsyncClient(base_url='http://localhost:8000')`
5. **`frontend/chatbot/core.py`** - Two clients:
   - `self.api_client = httpx.AsyncClient(base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT)`
   - `self.ollama_client = httpx.AsyncClient(base_url=config.OLLAMA_HOST, timeout=60.0)`

---

## Endpoint Summary Table

| Method | Endpoint | File | Line | Purpose |
|--------|----------|------|------|---------|
| GET | `/models` | `models.py` | 111 | List all models/plugins |
| GET | `/models` | `models.py` | 111 | List all models/plugins |
| GET | `/models/{model_uid}` | `jobs.py` | 175 | Get model name |
| GET | `/models/{model_uid}` | `job_details.py` | 251 | Get model info |
| GET | `/models/{model_uid}/info` | `model_details.py` | 49 | Get model metadata (primary) |
| GET | `/models/{model_uid}` | `model_details.py` | 53 | Get model metadata (fallback) |
| GET | `/servers` | `models.py` | 121 | List all servers |
| GET | `/servers/{model_uid}/status` | `models.py` | 132 | Check model server status |
| GET | `/servers/{model_uid}/status` | `model_details.py` | 71 | Check model server status |
| GET | `/{endpoint}/task_schema` | `chatbot/core.py` | 123 | Get task schema for endpoint |
| POST | `/{endpoint}` | `chatbot/core.py` | 301 | Submit job to endpoint |
| POST | `/api/generate` (Ollama) | `chatbot/core.py` | 357 | Call Granite model |

---

## Notes

1. **Base URL**: All RescueBox API calls use `http://localhost:8000` (or `config.RESCUEBOX_HOST` for chatbot)
2. **Ollama Base URL**: Granite model calls use `http://localhost:11434` (or `config.OLLAMA_HOST`)
3. **Error Handling**: All calls use `raise_for_status()` to raise exceptions on HTTP errors
4. **Timeouts**: 
   - Default: 30 seconds for API client
   - Ollama: 60 seconds
   - Server status: 5 seconds (explicit timeout in model_details.py)
5. **No Shared Client**: Each page/module creates its own HTTP client instance (no global singleton)

---

## Potential Improvements

1. **Shared Client**: Could create a shared HTTP client instance to avoid multiple connections
2. **Base URL Configuration**: Could centralize base URL configuration instead of hardcoding `http://localhost:8000`
3. **Error Handling**: Could add retry logic or more sophisticated error handling
4. **Caching**: Some endpoints (like `/models`) could benefit from response caching

