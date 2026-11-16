# RescueBox Desktop - Frontend Guide

RescueBox Desktop provides a modern, responsive web application built entirely in Python using [NiceGUI](https://nicegui.io/). This unified Python frontend eliminates Electron/JavaScript overhead and integrates seamlessly with the FastAPI backend services and Ollama / IBM Granite LLMs.

---

## 1. Quick Start

### Running the Application

From the repository root with your virtual environment activated:

```bash
# Run the NiceGUI frontend
python -m frontend.main
```

The application defaults to serving on `http://127.0.0.1:8080` (or `APP_PORT` defined in `frontend/config.py`).

### Environment Configuration

Key settings can be configured via environment variables or in `frontend/config.py`:
- `APP_PORT`: NiceGUI listening port (default: `8080`).
- `BACKEND_URL`: URL of the RescueBox FastAPI backend service (default: `http://127.0.0.1:8000`).
- `LOG_LEVEL`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- `FILTER_ENABLED`: Enables forensic scope validation on natural language prompts (default: `True`).

---

## 2. Architecture & Subsystems

RescueBox enforces a clear separation of concerns between presentation, reusable UI components, domain AI logic, and persistence:

```
┌────────────────────────────────────────────────────────┐
│  frontend/pages/                                       │  <-- PRESENTATION & ROUTES
│  - NiceGUI page routes (@ui.page)                      │      (/, /chatbot, /jobs, /models, /logs)
│  - Full page layouts, user events, and shells          │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
                ▼                        ▼
┌──────────────────────────────┐ ┌───────────────────────┐
│  frontend/components/        │ │  frontend/chatbot/    │  <-- DOMAIN / AI LOGIC
│  - Reusable UI widgets       │ │  - Ollama & Granite   │      (Headless pure Python,
│  - Form field builders       │ │  - Tool schemas & NLP │       tool registries & prompts)
│  - Result previews & modals  │ │  - Request filters    │
└───────────────┬──────────────┘ └───────────┬───────────┘
                │                            │
                ▼                            ▼
┌────────────────────────────────────────────────────────┐
│  frontend/database/ & frontend/utils/                  │  <-- DATA & INFRASTRUCTURE
│  - SQLite repositories (jobs.db, chat.db, cases.db)    │      (Storage, browser dialogs,
│  - Cross-cutting utilities (logging, job progress)     │       paths, theme tokens)
└────────────────────────────────────────────────────────┘
```

### Directory Summary

- **`frontend/pages/`**: Full-screen page modules and routes (`/` home, `/chatbot`, `/jobs`, `/models`, `/logs`, `/about`, `/demo`).
- **`frontend/components/`**: Reusable UI elements (form generators, results preview renderers, navigation bars, breadcrumbs).
- **`frontend/chatbot/`**: Headless AI domain logic (`ChatbotCore`, `MessageHandler`, `ToolRegistry`, multi-tool sequencing, and request filters).
- **`frontend/database/`**: SQLite database clients (`JobDB`, `CaseDB`, `ChatHistoryDB`) and validation schemas.
- **`frontend/utils/`**: Shared infrastructure helpers (`storage.py`, `job_progress.py`, `browser.py`, `paths.py`, `logging.py`).

---

## 3. Core Documentation Guides

Detailed technical guides and runtime walkthroughs are located under **[`frontend/docs/`](docs/)**:

| Document | Purpose |
| :--- | :--- |
| **[docs/pages-architecture.md](docs/pages-architecture.md)** | Comprehensive guide to `frontend/pages/` routes, layout structure, and page shells. |
| **[docs/chatbot-architecture.md](docs/chatbot-architecture.md)** | Architectural deep-dive separating `frontend/chatbot/` (AI brain) from `frontend/pages/chatbot/` (UI face). |
| **[docs/ui-flow.md](docs/ui-flow.md)** | Step-by-step runtime execution journeys (chat prompts, slash commands, forms, results, pipelines). |
| **[docs/style-theme.md](docs/style-theme.md)** | Theme tokens, color palettes, dark mode preferences, and styling conventions. |
| **[docs/refactor-items.md](docs/refactor-items.md)** | Active refactoring backlog and architectural milestone history. |
| **[docs/README.md](docs/README.md)** | Index of documentation guides and runtime class inventory. |

---

## 4. Testing

RescueBox includes a comprehensive test suite covering unit behaviors, UI workflows, and database interactions:

```bash
# Run all unit tests
pytest frontend/tests/unit/

# Run specific component or page tests
pytest frontend/tests/unit/test_message_flow_coordinator.py
pytest frontend/tests/unit/test_job_background_submission.py

# Run UI integration tests
# (On Windows PowerShell)
$env:RUN_INTEGRATION="1"; pytest frontend/tests/integration/test_ui_integration.py

# (On Linux / macOS Bash)
RUN_INTEGRATION=1 pytest frontend/tests/integration/test_ui_integration.py
```

---

## 5. Development Guidelines

1. **Keep UI Decoupled from Business Logic**: NiceGUI elements (`ui.label`, `ui.button`, DOM callbacks) belong strictly in `frontend/pages/` and `frontend/components/`. Domain services (`frontend/chatbot/`) must remain UI-agnostic.
2. **Keep Modules Focused**: When a module exceeds ~400 lines, extract helper classes or services into focused submodules.
3. **Preserve Public Exports**: When refactoring, maintain stable public APIs on `__init__.py` barrels to avoid breaking external callers.
4. **Use Established Services**: Prefer existing repositories (`get_job_db()`, `get_chat_history_db()`, `DatabaseService`) rather than writing ad-hoc raw SQLite queries.
