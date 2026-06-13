# Frontend refactor items (comprehensive audit)

This document consolidates a broad review of `frontend/` into an actionable backlog.
It is organized by runtime flow and subsystem, with concrete PR-sized first slices.

## Scoring

- **Impact:** expected reduction in defects/maintenance cost.
- **Risk:** chance of behavior regression while refactoring.
- **Effort:** relative implementation size (`S`, `M`, `L`).

## Priority summary

1. **P0 (do first):** schema/bootstrap unification, rerun-path correctness, test boundary cleanup.
2. **P1:** split remaining large modules in chat/pipeline and database internals.
3. **P2:** compatibility shim removal, docs/API cleanup, optional CI policy gates.

---

## P0 — high value / high leverage

| Area | Refactor item | Impact | Risk | Effort | First slice |
|------|---------------|--------|------|--------|-------------|
| Database foundation | Unify `jobs.db` schema ownership and remove parallel DDL paths (`JobDatabaseSchema` vs `jobs_runtime_*` vs migrations). | High | Medium | M-L | Make `JobDB._create_schema` and `initialize_schema` use one canonical helper set; ensure pipeline columns present on fresh DB. |
| Database startup | Unify bootstrap behavior of `init_database()` and lazy `get_job_db()`. | High | Medium | M | Add single bootstrap function used by both code paths. |
| Chat rerun flow | Unify rerun metadata resolution across `/chatbot?rerun=`, history UI rerun, and page-level rerun methods. | High | Medium | S-M | Add one `resolve_rerun_payload(...)` helper and use in all entry points. |

---

## P1 — core structural simplification

### Chat/pages flow

| Area | Refactor item | Impact | Risk | Effort | First slice |
|------|---------------|--------|------|--------|-------------| |
| Pipeline context | Eliminate triplicated “pipeline output path” logic across prompt, banner, and form injection flows. | High | Medium | M | Add shared `pipeline_context.py` helper and wire one call site first (`ui_flow`). |
| Job orchestration | Continue consolidating job completion behavior into one service path (started with `JobLifecycleService`). | High | Medium | M | Route more completion/status/history branches through `JobLifecycleService`; keep `JobSubmissionOrchestrator` as UI glue. |
| Chat flow overlap | Reduce overlap among `MessageFlowCoordinator`, `MessageProcessor`, and `ResultProcessor`. | Medium-High | Medium | M | Ensure one shared `FormSubmitHandler` instance and one form-load route per page session. |
| Package surface | Slim `pages/chatbot/__init__.py` so it stops acting as a broad barrel across UI/domain/DB. | Medium | Low | S-M | Remove DB exports from package surface; import DB directly where needed. |
| Pipeline handler | Keep `pipeline.py` focused on UI control; keep planning/filter logic in helper modules. | Medium | Medium | M | Build on `pipeline_planner.py` extraction with dialog/filter helper extraction. |

### Database/utils layer

| Area | Refactor item | Impact | Risk | Effort | First slice |
|------|---------------|--------|------|--------|-------------|
| `chat_history_db.py` | Split large class into migrations + query/repository helpers. | High | Medium | L | Extract migrations and row mapping modules; preserve public API. |
| `jobs.db` singleton model | Reduce multiple long-lived singleton connections to one provider strategy. | High | Medium | M | Introduce shared connection provider for `JobDB`, `CaseDB`, `ChatHistoryDB`. |
| User/case scoping | Align scoping rules between jobs and chat history (currently asymmetric). | High | High | M | Pass user/case scoping from page boundary; avoid hidden storage reads deep in DB queries. |
| Exception boundaries | Stop broad tuple coupling (`DB_ERRORS` including UI-like exceptions) and standardize DB exception taxonomy. | Medium-High | Medium | M | Introduce explicit DB exception classes and narrow catches in DB modules. |
| `utils/storage.py` | Split session storage helpers from case/DB coupling. | Medium-High | Medium | M | Move pure session key helpers into dedicated module; keep compat re-exports. |
| `model_cache.py` | Align with `BaseDatabase` patterns; remove destructive schema reset behavior. | Medium | Medium | S-M | Add additive migration path and DB pragma parity with other DB modules. |

### Components/tests/docs

| Area | Refactor item | Impact | Risk | Effort | First slice |
|------|---------------|--------|------|--------|-------------|
| Component shim cleanup | Remove test-driven compatibility shims from `components/*/__init__.py` barrels. | High | Medium | M | Retarget tests to concrete modules, then remove one shim group at a time. |
| Large render modules | Split `components/results/text.py` and `components/forms/field_builders.py` by domain responsibilities. | Medium-High | Medium | M | Extract one renderer/builder cluster each while preserving public entrypoints. |
| Public API clarity | Define and document stable import map for `frontend.components` and notifications path. | Medium | Low | S | Add short import policy section in docs and adjust one ambiguous export (`navbar` alias semantics). |
| Dead/compat exports | Remove no-op or stale compat exports (`setup_component_imports`, legacy aliases) after grep-based validation. | Medium | Low | S | Remove one symbol group per PR with targeted tests. |

---

## Known large-file hotspots

- `frontend/components/results/text.py`
- `frontend/components/forms/field_builders.py`

---

## Test guardrails to add/expand

| Refactor area | Must-have validation |
|---------------|----------------------|
| Schema/bootstrap changes | Fresh DB bootstrap parity test across all entrypoints; assert expected tables/indexes/columns. |
| Rerun flow | Unit tests for all rerun entrypaths using persisted `tool_calls` metadata shapes. |
| Job orchestration lifecycle | Background submit success/failure tests with history/status persistence assertions. |
| Pipeline chaining | Chained-step tests ensuring output-path injection and metadata filter behavior still match existing flows. |
| Conftest/test-boundary cleanup | CI run profile proving unit suite excludes integration markers by default. |

---

## Suggested implementation sequence

1. **P0 schema/bootstrap + rerun correctness + test boundary cleanup.**
2. **Chat flow consolidation** (`tool_config` split, shared pipeline context, single form-submit path).
3. **Database internals cleanup** (`chat_history_db` split, exception taxonomy, connection provider).
4. **Component/test shim cleanup** and large renderer/builder decomposition.
5. **Docs/API stabilization** and optional CI policy gates.

---

## Notes

- Keep behavior stable first; prefer extraction/re-exports before API-breaking moves.
- Land changes in small PR slices with explicit regression tests.
- For risky items (schema/scoping), gate with migration/compat tests before broader cleanup.
