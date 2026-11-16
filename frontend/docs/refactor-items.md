# Frontend refactor items & roadmap audit

This document tracks the refactor backlog for `frontend/`, recording completed improvements and active tasks with their priority, impact, and implementation notes.

## Scoring

- **Impact:** expected reduction in defects/maintenance cost.
- **Risk:** chance of behavior regression while refactoring.
- **Effort:** relative implementation size (`S`, `M`, `L`).

---

## Status Summary

| Area | Total Items | Completed | Pending Backlog |
|------|-------------|-----------|-----------------|
| **P0 — High Value / Bootstrap** | 3 | 3 | 0 |
| **P1 — Chat / Pages Flow** | 5 | 5 | 0 |
| **P1 — Database / Utils Layer** | 6 | 3 (2 done, 1 by design) | 3 |
| **P2 — Components / Tests / Docs** | 4 | 3 | 1 |

> **Note on Deletion:** This document should **not** be removed yet. While all P0 items, chat/orchestration flow items, and component decomposition items have been completed, database items around `chat_history_db.py`, `model_cache.py`, and scoping remain.

---

## P0 — High Value / High Leverage

| Status | Area | Refactor Item | First Slice / Resolution |
|:------:|------|---------------|--------------------------|
| ✅ **COMPLETED** | Database foundation | Unify `jobs.db` schema ownership and remove parallel DDL paths. | `JobDB._create_schema()` and `initialize_schema()` now both use canonical `_initialize_schema_sync()` running `jobs_runtime_*` statements and `ensure_all_job_columns()`. |
| ✅ **COMPLETED** | Database startup | Unify bootstrap behavior of `init_database()` and lazy `get_job_db()`. | Both `init_database()` and `get_job_db()` route through `JobDB` instantiation and sync schema initialization. |
| ✅ **COMPLETED** | Chat rerun flow | Unify rerun metadata resolution across `/chatbot?rerun=`, history UI rerun, and page-level rerun methods. | All entry points delegate to `ChatbotPage.handle_rerun_tool()` and `_resolve_rerun_arguments()`, with parameter fallback from `JobDB` request snapshot when history row omits them. |

---

## P1 — Core Structural Simplification

### Chat / Pages Flow

| Status | Area | Refactor Item | First Slice / Resolution |
|:------:|------|---------------|--------------------------|
| ✅ **COMPLETED** | Pipeline context | Eliminate triplicated “pipeline output path” logic across prompt, banner, and form injection flows. | Extracted `frontend/chatbot/pipeline_context.py` with `get_pipeline_output_path()`, `inject_pipeline_path()`, and `extract_output_path()`. Wired into `ui_builder.py`, `ui_flow.py`, and `tool_config.py`. |
| ✅ **COMPLETED** | Job orchestration | Consolidate job completion behavior into dedicated service path. | Extracted `frontend/pages/chatbot/handlers/job_lifecycle_service.py` (`JobLifecycleService`). Handles `create_tracked_job`, `record_job_started`, `complete_successful_submission`, and `mark_submission_failed`. |
| ✅ **COMPLETED** | Chat flow overlap | Consolidate chat orchestration into `MessageFlowCoordinator` and `ResultProcessor`. | Extracted `ChatUIDelegate` protocol (`ui_delegate.py`). Consolidated `MessageProcessor` into `MessageFlowCoordinator`. Reused single `FormSubmitHandler` instance across `ResultProcessor`. |
| ✅ **COMPLETED** | Package surface | Slim `pages/chatbot/__init__.py` to remove broad barrel coupling. | Removed direct database instance exports from package surface; DB singletons imported directly where needed. |
| ✅ **COMPLETED** | Pipeline handler | Keep `pipeline.py` focused on UI control; keep planning/filter logic in helper modules. | Planning extracted to `frontend/pages/chatbot/handlers/pipeline_planner.py` (`plan_next_pipeline_step`, `inject_filtered_paths_into_request`). |

### Database / Utils Layer (Active Backlog)

| Status | Area | Refactor Item | Impact | Risk | Effort | Pending Work / Resolution |
|:------:|------|---------------|:------:|:----:|:------:|---------------------------|
| ⏳ **PENDING** | `chat_history_db.py` | Split large class (~24KB) into migrations + query/repository helpers. | High | Medium | L | Extract migrations and row mapping modules (`chat_history_queries.py`, `chat_history_migrations.py`) following the `job_db` split pattern while preserving public API. |
| 🛡️ **BY DESIGN** | `jobs.db` connection model | Evaluate separate connections for `JobDB`, `CaseDB`, `ChatHistoryDB`. | — | — | — | **Kept separate by design.** Separate `sqlite3.Connection` instances are desirable to maximize SQLite WAL mode concurrency (readers do not block writers) and guarantee transaction isolation without cursor collisions in async coroutines. Standardized via `BaseDatabase`. |
| ⏳ **PENDING** | User/case scoping | Align scoping rules between jobs and chat history (currently asymmetric). | High | High | M | Pass user and case IDs explicitly from page boundaries instead of implicit session reads deep inside DB queries. |
| ✅ **COMPLETED** | Exception boundaries | Stop broad tuple coupling (`DB_ERRORS = (*UI_RENDER_ERRORS, sqlite3.Error)`). | Medium-High | Medium | M | Decoupled `db_exceptions.py` completely from `UI_RENDER_ERRORS`; defined domain exceptions (`DatabaseError`, `RecordNotFoundError`, `SchemaError`, `DatabaseConnectionError`). |
| ✅ **COMPLETED** | `utils/storage.py` | Split session storage helpers from case/DB coupling. | Medium-High | Medium | M | Extracted pure session state accessors to `frontend/utils/session.py` (zero DB imports); isolated CaseDB queries to `frontend/utils/case_context.py`; preserved compatibility in `storage.py`. |
| ⏳ **PENDING** | `model_cache.py` | Align with `BaseDatabase` patterns; remove destructive schema reset behavior. | Medium | Medium | S-M | Replace `DROP TABLE models` with additive migrations and adopt WAL / busy timeout pragmas from `BaseDatabase`. |

---

## P2 — Components / Tests / Documentation

| Status | Area | Refactor Item | Impact | Risk | Effort | First Slice / Resolution |
|:------:|------|---------------|:------:|:----:|:------:|--------------------------|
| ✅ **COMPLETED** | Component shim cleanup | Remove test-driven compatibility shims from `components/*/__init__.py` barrels. | High | Medium | M | Removed `history_panel = sys.modules[__name__]` and aliases from `components/chat/__init__.py`; retargeted `test_chat_components.py` directly to concrete modules. |
| ✅ **COMPLETED** | Large render modules | Split `components/results/text.py` and `components/forms/field_builders.py`. | Medium-High | Medium | M | Extracted `text_modal.py`, `text_search.py`, `batch_text.py` from `text.py` (337 -> 64 lines); extracted `path_inputs.py` and `parameter_fields.py` from `field_builders.py` (356 -> 72 lines). Re-exports preserved. |
| ✅ **COMPLETED** | Public API clarity & Docs | Update docs to map user usage flow scenarios to current code implementations. | Medium | Low | S | Comprehensive user journey scenarios documented in `docs/ui-flow.md` and class index updated in `docs/README.md`. |
| ⏳ **PENDING** | Dead/compat exports | Remove no-op or stale compat exports after grep-based validation across plugins and tests. | Medium | Low | S | Audit and clean up unused legacy aliases. |

---

## Known Large-File Hotspots (Active Tracking)

- `frontend/database/chat_history_db.py` (~600 lines / 24 KB)

---

## Conclusion & Recommendation

**Do not remove this file.** It provides the engineering roadmap for the remaining backend/persistence technical debt. Keep this document updated as the active backlog for subsequent database and component decomposition milestones.
