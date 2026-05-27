# Frontend documentation (canonical)

Keep docs **small and current**. This index plus nine topic files are what we maintain (ten files including this README).

## Big picture

- **UI:** NiceGUI app in `frontend/main.py`; routes on `frontend/pages/*`; shared UI in `frontend/components/`.
- **Assistant (`/chatbot`):** User text → `MessageHandler.handle_message()` → slash commands or **`handle_smart_analyze()`** → **`ChatbotCore`** (alias of **`ThinChatbotCore`** in `frontend/chatbot/core.py`).
  - **Tool selection:** Ollama **`POST /api/chat`** on `OLLAMA_HOST` with `GRANITE_MODEL` (see `_call_ollama`).
  - **Plugins:** HTTP to **`RESCUEBOX_HOST`** — `GET {plugin}/{task}/task_schema`, `POST {plugin}/{task}` with JSON `inputs` / `parameters` (`frontend/chatbot/api_helpers.py` uses **`use_api_prefix=False`** for these paths so they match Typer-registered routes).
- **Models list in UI:** `ApiClient` in `frontend/api_client.py` defaults to paths under **`API_BASE_URL`** (usually `http://localhost:<port>/api`), e.g. **`GET /api/models`**, **`GET /api/servers`**, etc. (`frontend/config.py`).
- **Data:** SQLite under **`frontend/data/`** — one **`jobs.db`** file for both **jobs** and **chat history** tables; **`cache.db`** for cached model list; and dynamic per-pipeline index databases for tracking multi-step tool calls (`frontend/database/pipeline_job_index_db.py`). See database.md.

## Topic index

| Topic | Doc |
|--------|-----|
| End-to-end workflow (chat, tools, API) | [workflow.md](./workflow.md) |
| Look & feel (Maroon/Zinc/Medium-Gray, `Design` tokens, dark mode) | [style-theme.md](./style-theme.md) |
| Conversations, messages, rerun | [chat-history.md](./chat-history.md) |
| Job lifecycle, submission, polling | [jobs.md](./jobs.md) |
| SQLite files, storage | [database.md](./database.md) |
| Rendering API responses in the UI | [results.md](./results.md) |
| Forensic filter, `/analyze` | [pipeline-filter.md](./pipeline-filter.md) |
| Chatbot Architecture (modular package) | [chatbot-architecture.md](./chatbot-architecture.md) |
| Forms & Utilities Architecture | [forms-utils-architecture.md](./forms-utils-architecture.md) |
| Chat & Jobs Architecture | [chat-jobs-architecture.md](./chat-jobs-architecture.md) |
| Tests | [testing.md](./testing.md) |

## Code map

| Area | Main locations |
|------|----------------|
| Chat page | `frontend/pages/chatbot/ui.py` (`@ui.page('/chatbot')`) |
| Message routing | `frontend/chatbot/message_handler.py` (`MessageHandler`), `frontend/pages/chatbot/coordinator.py` |
| Granite API & Core | `frontend/chatbot/core.py` (Granite `<tool_code>` parsing, HTTP requests) |
| Form submit / orchestrator | `frontend/pages/chatbot/coordinator.py`, `frontend/pages/chatbot/handlers.py` |
| Job DB / chat DB | `frontend/database/job_db.py`, `chat_history_db.py` (same `jobs.db`) |
| Results UI | `frontend/components/results/` |
| Forms UI | `frontend/components/forms/` (Modular package) |
| Utilities | `frontend/utils/` (Modular package) |
| URL `?load_conversation=` / `?rerun=` | `frontend/pages/chatbot/ui.py` (`chatbot_page`, `_extract_chatbot_query_from_client`) |

## Related

- **Backend:** plugin routes and models router — `src/rb-api/rb/api/`.
- **Tests:** [testing.md](./testing.md); repo uses Poetry (`pyproject.toml`).
- **Refactor / complexity notes (non-canonical planning doc):** [frontend-complexity-review.md](./frontend-complexity-review.md).
