# Frontend documentation (canonical)

Keep docs **small and current**. This index plus nine topic files are what we maintain (ten files including this README).

## Big picture

- **UI:** NiceGUI app in `frontend/main.py`; routes on `frontend/pages/*`; shared UI in `frontend/components/`.
- **Assistant (`/chatbot`):** User text → `MessageHandler.handle_message()` → slash commands or **`handle_smart_analyze()`** → **`ChatbotCore`** (alias of **`ThinChatbotCore`** in `frontend/chatbot/core.py`).
  - **Tool selection:** Ollama **`POST /api/chat`** on `OLLAMA_HOST` with `GRANITE_MODEL` (see `_call_ollama`).
  - **Plugins:** HTTP to **`RESCUEBOX_HOST`** — `GET {plugin}/{task}/task_schema`, `POST {plugin}/{task}` with JSON `inputs` / `parameters` (`frontend/chatbot/api_helpers.py` uses **`use_api_prefix=False`** for these paths so they match Typer-registered routes).
- **Models list in UI:** `ApiClient` in `frontend/api_client.py` defaults to paths under **`API_BASE_URL`** (usually `http://localhost:<port>/api`), e.g. **`GET /api/models`**, **`GET /api/servers`**, etc. (`frontend/config.py`).
- **Data:** SQLite under **`frontend/data/`** — one **`jobs.db`** file for both **jobs** and **chat history** tables; **`cache.db`** for cached model list (`frontend/database/__init__.py`). See [database.md](./database.md).

## Topic index

| Topic | Doc |
|--------|-----|
| End-to-end workflow (chat, tools, API) | [workflow.md](./workflow.md) |
| Look & feel (Tailwind, dark mode, layout) | [style-theme.md](./style-theme.md) |
| Conversations, messages, rerun | [chat-history.md](./chat-history.md) |
| Job lifecycle, submission, polling | [jobs.md](./jobs.md) |
| SQLite files, storage | [database.md](./database.md) |
| Rendering API responses in the UI | [results.md](./results.md) |
| Forensic filter, `/analyze` | [pipeline-filter.md](./pipeline-filter.md) |
| Tests | [testing.md](./testing.md) |

## Code map

| Area | Main locations |
|------|----------------|
| Chat page | `frontend/pages/chatbot/chatbot.py` (`@ui.page('/chatbot')`) |
| Message routing | `frontend/chatbot/message_handler.py` (`MessageHandler`) |
| Granite + forms + submit | `frontend/chatbot/core.py`, `orchestrator.py`, `api_helpers.py` |
| Coordinator | `frontend/pages/chatbot/handlers/message_flow_coordinator.py` |
| Form submit / results | `frontend/pages/chatbot/handlers/form_submit_handler.py`, `job_submission_orchestrator.py` |
| Job DB / chat DB | `frontend/database/job_db.py`, `chat_history_db.py` (same `jobs.db`) |
| Results UI | `frontend/components/results/` |
| URL `?load_conversation=` / `?rerun=` | `frontend/pages/chatbot/parameter_handlers.py` |

## Related

- **Backend:** plugin routes and models router — `src/rb-api/rb/api/`.
- **Tests:** [testing.md](./testing.md); repo uses Poetry (`pyproject.toml`).
- **Refactor / complexity notes (non-canonical planning doc):** [frontend-complexity-review.md](./frontend-complexity-review.md).
