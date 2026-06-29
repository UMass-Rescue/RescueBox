# UI flow (quick one-page)

Fast reference for how users move through the frontend and which code paths run.

## Run

1. Start backend (plugin APIs and `/api/models` on `RESCUEBOX_HOST`).
2. Start UI: `poetry run python -m frontend.main` (NiceGUI on `APP_PORT`).
3. Optional: Ollama (`OLLAMA_HOST`, `GRANITE_MODEL`) for natural-language tool selection.

## Startup path (`frontend/main.py`)

1. `init_db()` initializes frontend DBs (`frontend/data/`).
2. `import frontend.pages` registers all `@ui.page` routes.
3. `prefetch_and_cache_models()` warms plugin/model cache.
4. `ui.run(..., show=APP_SHOW_BROWSER)` starts the app.

## Main routes

- `/` -> case create/load (`pages/home.py`, `home_dashboard.py`)
- `/case` -> active case overview (`home_case_overview.py`)
- `/chatbot` -> assistant UI (`pages/chatbot/routes.py`, `chat_page.py`)
- `/models` -> plugin/model list (`pages/models.py`)
- `/jobs` and `/jobs/{id}` -> job list/details (`pages/jobs/*`)

## Core user flow (case -> chat -> form -> job -> results)

1. User creates/loads case -> `set_active_case_id` (stored in `app.storage.user`).
2. User opens `/chatbot` -> `ChatbotPage.render()` builds UI/controller stack.
3. User sends message -> `MessageFlowCoordinator` -> `MessageProcessor` -> `MessageHandler`.
4. Tool selection:
   - slash command: direct tool path
   - natural language: `handle_smart_analyze` -> Granite/Ollama via `ChatbotCore`
5. Form display -> `load_and_show_form()` -> `fetch_task_schema()` -> `FormGenerator`.
6. Submit -> `FormSubmitHandler.submit_form()` (active case required) -> `JobSubmissionOrchestrator.submit_job()`.
7. API POST -> `core.submit_job()` / `api_helpers.post_job()` -> persist status in `job_db`.
8. Results render -> `show_results()` using `components/results/`.
9. If pipeline has more steps -> `PipelineHandler` schedules next form and chains output to input.

## Pipeline logic (multi-step)

- `multi_tool_calls` are processed step-by-step (not all at once).
- Output chaining uses:
  - `multi_tool_handler.extract_output_path`
  - `multi_tool_handler.chain_output_to_input`
- Optional metadata filtering applies only for age/gender-capable outputs.

## State and storage

- Session/user/theme/drafts: `utils/storage.py` (`app.storage.user`)
- Active case id: gates job submission and scopes chat/jobs
- Jobs + chat history: `frontend/data/jobs.db`
- Model cache: `frontend/data/cache.db`

## Key config

- `APP_PORT` -> frontend port
- `API_BASE_URL` -> `/api/*` endpoints
- `RESCUEBOX_HOST` -> plugin schema/job endpoints
- `OLLAMA_HOST`, `GRANITE_MODEL` -> NL tool selection
- `APP_DARK_MODE` + saved prefs -> theme behavior

## Related

- [README.md](./README.md)
- [style-theme.md](./style-theme.md)
