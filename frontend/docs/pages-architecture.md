# Pages Architecture: Presentation Layer Guide

This document describes the role, organization, and scope of `frontend/pages/` within the RescueBox frontend.

---

## 1. Architectural Scope of `frontend/pages/`

`frontend/pages/` represents the **Presentation & Routing Layer** of the application. Every file and module in this directory is dedicated to user-facing web interface concerns:

1. **NiceGUI Page Routes**: Registering URL endpoints via the `@ui.page(...)` decorator.
2. **HTML & Tailwind CSS Layouts**: Defining responsive layouts with NiceGUI elements (`ui.column()`, `ui.row()`, `ui.card()`, `ui.grid()`) and Tailwind classes.
3. **Interactive User Events**: Handling user inputs, form submissions, button clicks (`on_click`), and interactive dialogs.
4. **Client Session & View Lifecycle**: Managing client-specific state, notification toasts (`ui.notify`), scroll positioning, and page shells.

---

## 2. Directory & Route Breakdown

| Route / Subsystem | Primary Files in `frontend/pages/` | Purpose & Components |
| :--- | :--- | :--- |
| **Home / Dashboard (`/`)** | `home.py`<br>`home_dashboard.py`<br>`home_case_overview.py` | • Main dashboard overview<br>• Active case selection & details card<br>• Recent jobs table and quick action links |
| **Chatbot (`/chatbot`)** | `chatbot/routes.py`<br>`chatbot/chat_page.py`<br>`chatbot/ui_builder.py`<br>`chatbot/history_ui.py`<br>`chatbot/pickers.py` | • Conversational AI forensic assistant interface<br>• Message scroll area and input prompt field<br>• Conversation history sidebar drawer<br>• Dynamic tool invocation and interactive pickers |
| **Jobs (`/jobs`)** | `jobs/list.py`<br>`jobs/details.py`<br>`jobs/components.py` | • Active, queued, and completed jobs listing<br>• Job progress, logs inspection, and status badges<br>• Job re-run and artifact download actions |
| **Models (`/models`)** | `models.py` | • Installed AI models inventory<br>• Model capability cards, parameters, and status indicators |
| **Logs (`/logs`)** | `logs.py` | • Live application and backend log viewer<br>• Log level filtering (INFO, WARN, ERROR) and auto-refresh |
| **About (`/about`)** | `about.py`<br>`licenses_copyright.py` | • System information, dependencies, and license attribution |
| **Demos / Walkthroughs (`/demo`)** | `demo.py`<br>`demo_quick_start.py`<br>`demo_*_walkthrough.py` | • Interactive step-by-step feature walkthroughs<br>• Preset demonstration workflows |
| **Shared Shell & Wrappers** | `page_shell.py`<br>`page_utils.py` | • Shared top navigation bar (`create_navbar()`)<br>• Theme toggle and consistent page container shells |

---

## 3. How `frontend/pages/` Fits into the System Architecture

RescueBox maintains a clear boundary between presentation, components, domain logic, and persistence:

```
┌────────────────────────────────────────────────────────┐
│  frontend/pages/                                       │  <-- PRESENTATION & ROUTES
│  - Full page definitions (@ui.page routes)             │      (NiceGUI layout, page shells,
│  - User interaction handlers and event routing         │       route query params, toasts)
└───────────────┬────────────────────────┬───────────────┘
                │                        │
                ▼                        ▼
┌──────────────────────────────┐ ┌───────────────────────┐
│  frontend/components/        │ │  frontend/chatbot/    │  <-- HEADLESS DOMAIN LOGIC
│  - Reusable UI widgets       │ │  - Ollama & Granite   │      (Pure Python, zero DOM,
│  - Form field builders       │ │  - Tool schemas & NLP │       tool registries & NLP)
│  - Result previews / modals  │ │  - Request filters    │
└───────────────┬──────────────┘ └───────────┬───────────┘
                │                            │
                ▼                            ▼
┌────────────────────────────────────────────────────────┐
│  frontend/database/ & frontend/utils/                  │  <-- DATA & INFRASTRUCTURE
│  - SQLite databases (jobs.db, chat_history.db, case.db)│      (Storage, logging, paths)
└────────────────────────────────────────────────────────┘
```

- **`frontend/pages/` vs. `frontend/components/`**: Pages assemble full views and handle routes; components are reusable building blocks (e.g. form generators, result dispatchers, breadcrumbs) shared across pages.
- **`frontend/pages/` vs. `frontend/chatbot/`**: Pages handle NiceGUI UI interaction; `frontend/chatbot/` contains headless AI model communication, tool registries, and prompt engineering without any UI dependencies.
- **`frontend/pages/` vs. `frontend/database/`**: Pages query databases through services (`JobDB`, `CaseDB`, `ChatHistoryDB`) to display data, but do not define database schemas or perform raw SQL/table management.
