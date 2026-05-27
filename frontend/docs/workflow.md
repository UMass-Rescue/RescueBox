# Workflow

## Routes (implemented)

| Route | Module | Role |
|-------|--------|------|
| `/chatbot` | `frontend/pages/chatbot/chatbot.py` | Assistant: messages, tool selection, forms, results |
| `/models` | `frontend/pages/models/models.py` | Browse plugins, open details |
| `/models/{model_uid}/details` | `model_details.py` | Model metadata and status |
| `/jobs` | `frontend/pages/jobs/jobs.py` | Job list |
| `/jobs/{job_id}` | `frontend/pages/jobs/job_details.py` | Job detail |

## Assistant path (happy path)

1. User sends text → `MessageProcessor` / **`MessageFlowCoordinator`** → **`MessageHandler.handle_message()`** → **`handle_slash_command()`** or **`handle_smart_analyze()`** (`frontend/chatbot/message_handler.py`).
2. **Granite (Ollama):** `ChatbotCore.call_granite_model_direct()` → `_call_ollama()` → tool call list; parsing in `frontend/chatbot/granite.py` / `tool_config` advanced prompt.
3. **Schema:** `fetch_task_schema()` → **`GET`** `{endpoint}/task_schema` on **`RESCUEBOX_HOST`**.
4. **Form:** `FormGenerator` / `chatbot_forms` build inputs from `TaskSchema`; validation **`validate_request_body`** (`frontend/utils/validators.py`).
5. **Run:** **`post_job()`** → **`POST`** same `{endpoint}` with `{"inputs": ..., "parameters": ...}`; response normalized to **`ResponseBody`** in **`submit_job_orchestrator`** (`frontend/chatbot/orchestrator.py`).
6. **UI:** `show_results` / result cards; persistence via chat history + `JobDB` (see [chat-history.md](./chat-history.md), [jobs.md](./jobs.md)).

## Multiple tools in one reply

Sequential execution: **`frontend/chatbot/multi_tool_handler.py`**.

## Models without NL chat

Tool picker: **`frontend/pages/chatbot/pickers.py`** → same schema → form → POST.

## URL parameters

Handled by **`chatbot_page`** in **`frontend/pages/chatbot/ui.py`** (NiceGUI route kwargs plus `_extract_chatbot_query_from_client` for SPA navigations):

- `?load_conversation=<uuid>`
- `?rerun=<message_id>`

## Config (env-aware)

**`ChatbotConfig`** (`frontend/chatbot/config.py`): `OLLAMA_HOST`, `GRANITE_MODEL`, `RESCUEBOX_HOST`, `TIMEOUT`, `FILTER_ENABLED`, `POLL_INTERVAL`. Overrides via env (see `ChatbotConfig.__init__`).
