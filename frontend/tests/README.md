# Frontend tests

## Quick commands

```bash
# Unit tests (default CI-friendly)
poetry run pytest frontend/tests/unit -q

# Integration (requires backend / Ollama / env — see integration/README.md)
set RUN_INTEGRATION=1
poetry run pytest frontend/tests/integration -v --tb=short

# Lint
poetry run pylint frontend
```

## Layout

| Directory | Purpose |
|-----------|---------|
| `unit/` | Fast tests; mocks for HTTP, NiceGUI storage, UI |
| `integration/` | NiceGUI `User` fixture, live API/Ollama when enabled |
| `scripts/` | Manual e2e / concurrent plugin scripts (not pytest collection) |

## New / updated unit modules (refactor coverage)

| Module | Covers |
|--------|--------|
| `test_api_client.py` | `ApiClient` paths, `json()` async/sync mocks, HTTP fallbacks |
| `test_utils_session_and_theme.py` | `ensure_session_user_id`, `ensure_active_case_id`, `apply_saved_theme` |
| `test_form_submit_handler.py` | Active case gate, case-notes cancel |
| `test_chatbot_handlers_package.py` | `handlers/` vs `ui_flow` export boundaries |
| `test_storage_reads.py` | `read_pipeline_job_id()` |
| `test_config_paths.py` | `DATA_DIR` / `LOG_FILE` / `APP_SHOW_BROWSER` |
| `test_chat_view_load_conversation.py` | `load_conversation` navigation errors |

See also: `README_CHATBOT_TESTS.md`, `integration/README.md`, `../docs/README.md`.
