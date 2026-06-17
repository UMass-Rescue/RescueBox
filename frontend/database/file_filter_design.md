Design: Persisted file_filters and job linkage
=============================================

Overview
--------
This document describes the design for persisting batch file filters (`file_filters`) in the application's database and linking them to `jobs` when users elect to save a filter for reuse or auditing.

Schema
------
- Table: `file_filters`
  - `id` TEXT PRIMARY KEY (UUID)
  - `name` TEXT NULL
  - `input_dir` TEXT NULL        -- normalized canonical directory
  - `filter_type` TEXT NOT NULL DEFAULT 'input' -- 'input' or 'output'
  - `paths_json` TEXT NULL      -- JSON array of relative paths (relative to `input_dir`) (used for input filters)
  - `patterns_json` TEXT NULL   -- JSON array of string/number patterns (used for output filters)
  - `owner_id` TEXT NULL
  - `source` TEXT NULL           -- e.g. "upload", "saved", "job"
  - `metadata` TEXT NULL         -- optional JSON blob
  - `is_active` INTEGER NOT NULL DEFAULT 1
  - `created_at` TEXT NOT NULL
  - `updated_at` TEXT NOT NULL


- Jobs table change:
  - Add nullable column `filterId` TEXT
  - Add a single index `filterID` on `filterId`
  - Semantics: when present, the job references a single persisted `file_filters.id` which may contain input paths, output patterns, or both (composite filter)

Rationale
---------
- Store relative paths (not absolute) to avoid machine-specific paths and to make filters portable across environments that share the same `input_dir` semantics.
- Use JSON (TEXT) for `paths_json` to keep writes and schema simple; switch to normalized `file_filter_paths` table only if queries over individual paths are required.
- Track `owner_id` and use session-based access control so users only see their own saved filters (or public/shared ones if marked via `metadata`).

APIs (sync DB helper)
---------------------
Implement `frontend.database.file_filter_store` exposing:
- `create_filter(name, input_dir: Path|str, paths: list[Path|str]=None, patterns: list[str|number]=None, filter_type: str='input', owner_id: Optional[str]=None, source: Optional[str]=None, metadata: Optional[dict]=None) -> str`
  - Normalize input_dir, convert paths to relative (for input filters), validate no path traversal, store JSON, return filter id
- `load_filter(filter_id: str) -> dict`
  - Returns dict with `input_dir` (Path) and `paths` (list[Path] resolved against input_dir)
- `list_filters(input_dir: Optional[Path|str]=None, owner_id: Optional[str]=None) -> list[dict]`
- `update_filter(filter_id, **kwargs) -> bool`
- `delete_filter(filter_id) -> bool`
-- `resolve_filter_for_job(batch_file_input: Optional[BatchFileInput], input_dir: Path, persist_if_requested: bool=False, owner_id: Optional[str]=None) -> Tuple[List[Path], Optional[str]]`
  - Returns resolved list of Paths and optional `filter_id` if persisted
  - Behavior:
    - If `batch_file_input` references `filter_id` => load saved filter
    - If `batch_file_input` contains inline file list:
      - If `persist_if_requested` or `save_as_name` present => create_filter and return id
      - Otherwise return resolved Paths without persisting
    - If none provided => return default: list(input_dir.iterdir()) filtered to files

- `resolve_output_filter_for_job(output_filter_input: Optional[BatchFileInput], persist_if_requested: bool=False, owner_id: Optional[str]=None) -> Tuple[List[Union[str,int,float]], Optional[str]]`
  - Returns resolved list of output patterns (strings or numeric descriptors) and optional `filter_id` if persisted
  - Behavior:
    - If `output_filter_input` references `filter_id` => load saved output filter (must have `filter_type` == 'output')
    - If `output_filter_input` contains inline pattern files:
      - Parse patterns from uploaded files (one per line); support simple numeric ranges like `>=0.5` or `5..10` if desired
      - If `persist_if_requested` or `save_as_name` present => create_filter(filter_type='output') and return id
      - Otherwise return resolved patterns without persisting
    - If none provided => return empty list (no output filtering)

Integration points
------------------
- `src/*` image-summary `summarize_images`:
  - Call `file_filter_store.resolve_filter_for_job(inputs.get("file_filter"), input_dir, persist_if_requested=False, owner_id=...)`
  - Call `file_filter_store.resolve_output_filter_for_job(inputs.get("output_filter"), persist_if_requested=False, owner_id=...)`
  - Use returned Paths for processing and returned output patterns to filter generated summaries.
  - If the user requests persisting both input and output filters together, call `file_filter_store.create_composite_filter(...)` and persist the returned `filterId` on the job.
  - When creating a Job (`JobDB.create_job`) accept optional `filter_id` and persist it in `jobs.filterId`.

- `JobDB` updates:
  - Add `filterId` to `JobRecord` model as Optional[str]
  - Persist/serialize it in `model_dump_for_db()` and SQL insert/update statements
  - Add a single index `filterID` on `filterId`



Validation & Security
---------------------
- Canonicalize `input_dir` (Path.resolve()) and ensure stored relative paths do not escape the directory (reject entries with `..` or resolved path not under `input_dir`).
- Limit size of `paths_json` to reasonable threshold (e.g., 10k entries or N MB) to prevent abuse.
- Enforce owner scoping when loading filters; support `is_active` or `public` flags via `metadata`.
 - For output filters, validate patterns (e.g., reject overly-complex regex by default) and normalize numeric range syntax if supported.
 - Ensure output patterns are safe (avoid regex ReDoS) and reasonably sized.

UX considerations
-----------------
 - Frontend: allow user to "Save these file selections" when they upload a batch or create a filter; call backend `create_filter` and include `filterId` with job creation.
 - Expose a small picker to select previously saved filters (passes `filterId` in BatchFileInput metadata).
- Provide a management view for saved filters (rename/delete/share).
 - Frontend should allow saving/selecting both an `input` filter and an `output` filter; when saving an output filter, offer options for pattern type (substring, regex, numeric range) and case-sensitivity.
 - When running the plugin, UI may offer "Apply saved input filter" and "Apply saved output filter" checkboxes; if the user chooses to persist both, the frontend will request creation of a composite filter and send a single `filterId` with the job creation which will be recorded on the job.

Testing
-------
- Unit tests:
  - create/load/update/delete flows
  - resolve_filter_for_job with inline list and saved filter id
  - resolve_output_filter_for_job with inline patterns and saved filter id
  - path traversal rejection
  - relative path resolution
 - Integration tests:
  - create a job with `filterId` and ensure job record contains link and `get_job_by_uid` can expose resolved filter (if desired)

Performance/Scaling notes
-------------------------
- For extremely large filters (tens of thousands of paths) consider separate normalized `file_filter_paths` table for join/query efficiency and pagination.
- Add caching for frequently used filters if resolution is expensive.


Utilities for job-runner and plugins
-----------------------------------
Provide a small, well-scoped utility surface that the job-runner and plugins can call to set, fetch and apply filters. These helpers live in `frontend.database.file_filter_store` (or a companion module `frontend.database.file_filter_utils.py`) and follow synchronous semantics consistent with `JobDB`.

Function signatures and behavior
 - set_job_filter(job_db: JobDB, job_uid: str, *, filter_id: Optional[str] = None, owner_id: Optional[str] = None) -> bool
  - Purpose: Associate a saved filter with an existing job record.
  - Behavior:
    - If `filter_id` provided: set `jobs.filterId = filter_id`.
    - Returns True on update success.

- get_job_filters(job_db: JobDB, job_uid: str) -> dict
  - Purpose: Load the filterId from the job record and return resolved values for the job-runner.
  - Returns dict:
    - `filter_id`: Optional[str]
    - `input_paths`: List[Path] (resolved absolute Paths to process; empty means "all files in input_dir")
    - `output_patterns`: List[Union[str,int,float]] (empty means no output filtering)
    - `metadata`: dict (filter metadata if present)
  - Behavior:
    - Read `job = await job_db.get_job_by_uid(job_uid)` (or sync variant).
    - If `job.filterId` present, load `file_filter = load_filter(job.filterId)` and resolve `paths_json` and `patterns_json` accordingly (join relative paths to job.input_dir if stored relative).
    - If `job.filterId` absent, attempt to extract inline lists from `job.request` (back-compat).

- resolve_input_files(input_dir: Path, input_paths: Optional[List[Path]]) -> List[Path]
  - Purpose: Normalize and validate the list of input files that should be processed.
  - Behavior:
    - If `input_paths` is None or empty: return [f for f in input_dir.iterdir() if f.is_file() and supported_extension].
    - Otherwise: canonicalize each path, ensure it is inside `input_dir` (reject or skip otherwise), and return the list.

- apply_output_filter(output_files: Iterable[Path], output_patterns: List[Union[str,int,float]], mode: str = 'substring', case_sensitive: bool = True) -> List[Path]
  - Purpose: Given generated output files (text summaries), return only those that match the provided patterns.
  - Behavior:
    - If `output_patterns` empty: return all `output_files`.
    - For each out_file:
      - Read text (skip unreadable files).
      - For each pattern in `output_patterns`:
        - If `mode == 'substring'`: check substring (respecting `case_sensitive`).
        - If `mode == 'regex'`: compile regex with a safe timeout/limit and match.
        - If `mode == 'numeric_range'`: parse pattern into operator/range and check numeric fields extracted from the summary or a numeric metadata field (plugins should document how numeric extraction works).
      - If any pattern matches, include file.
    - Return matched files.

- parse_output_pattern(pattern_str: str) -> Union[dict, str, float, int]
  - Purpose: Convert a raw pattern string into a structured descriptor (e.g., {'type':'range','op':'>=','value':0.5} or {'type':'substring','value':'foo'}).
  - Plugins may use this helper to interpret user-provided patterns consistently.

Example job-runner flow
1. When a job is created/started, call `get_job_filters(job_db, uid)` to get `input_paths` and `output_patterns`.
2. Call `resolve_input_files(input_dir, input_paths)` to get the concrete list of images to process.
3. Process images and write summaries to `output_dir`.
4. After processing, call `apply_output_filter(processed_output_files, output_patterns, mode=..., case_sensitive=...)` to get the final set of output files to report/store in job response.
5. If the user requested persistence of both filters at job submission, `set_job_filter(...)` would already have created and associated a composite `filterId` at job creation time.

Implementation notes
- Keep helpers synchronous to match `JobDB` patterns, but provide async wrappers if needed by async callers.
- Ensure all file IO includes safe error handling and size limits.
- For regex mode, restrict complexity and optionally compile with `re` and a manual timeout guard (or limit pattern length).
- Add logging at DEBUG level to trace filter resolution and application.

Testing for utilities
- Unit tests for `set_job_filter`, `get_job_filters`, `resolve_input_files`, `apply_output_filter`, and `parse_output_pattern` including edge cases:
  - Missing job/filter IDs
  - Path traversal attempts
  - Invalid pattern strings
  - Large pattern lists

Prompt processing integration
-----------------------------
Add a small prompt-processing helper that runs immediately after the Granite model returns validated tool calls and before a job is created. This helper detects any input/output filter specifications referenced by the tool call or implied by the prompt, resolves them (optionally persisting), and returns a single `filterId` that will be attached to the created job.

Recommended helper API (placed in `frontend.database.file_filter_utils` or inside `file_filter_store`):
- `process_prompt_for_filters(prompt: str, tool_call: dict, input_dir: Path, owner_id: Optional[str]=None, persist_if_requested: bool=False) -> Optional[str]`
  - Behavior:
    - Inspect `tool_call["arguments"]` for `file_filter` and `output_filter` fields (or other plugin-specific argument names).
    - Call `resolve_filter_for_job(...)` for the input filter and `resolve_output_filter_for_job(...)` for the output filter.
    - If both filters should be persisted together (user requested persist, or `persist_if_requested` True), call `create_composite_filter(...)` to create a single record containing both `paths_json` and `patterns_json`.
    - Return a single `filterId` (or None) that represents the resolved/persisted filters.

Where to call it
- Primary: `frontend/chatbot/message_handler.py::MessageHandler.handle_smart_analyze`
  - Placement: immediately after the Granite model call returns and tool calls are validated (before UI form rendering or job submission).
  - Rationale: at this point you have both the original prompt text and a structured `tool_call` object with parsed arguments.

- Secondary (defensive): In the job submission/orchestrator path just before `JobDB.create_job` or right after job creation to ensure the job has `filterId` persisted atomically. This is useful if the user picks filters in a form and the orchestration path is responsible for persisting them.

Pseudocode (integration)

```python
# inside MessageHandler.handle_smart_analyze, after validated_calls is produced
from frontend.database.file_filter_store import (
    resolve_filter_for_job, resolve_output_filter_for_job, create_composite_filter
)
from frontend.database.file_filter_utils import process_prompt_for_filters

owner = get_user_id_or_none()
for call in validated_calls:
    # attempt to detect and resolve/persist filters for this tool call
    filter_id = process_prompt_for_filters(
        prompt=user_message,
        tool_call=call,
        input_dir=Path(call.get('arguments', {}).get('input_dir', default_input_dir)),
        owner_id=owner,
        persist_if_requested=False
    )
    # attach to the tool_call so downstream orchestration can persist on job
    if filter_id:
        call['_resolved_filter_id'] = filter_id

# downstream, when creating a job (or immediately after create_job returns)
job = await job_db.create_job(... )  # existing call
filter_id = call.get('_resolved_filter_id')
if filter_id:
    # either pass filter_id into create_job (preferred) or update job after creation
    await set_job_filter(job_db, job.uid, filter_id=filter_id, owner_id=owner)
```

Notes and safety
- Prefer attaching `filterId` as part of the initial `create_job` insert when possible (add `filterId` to JobDB schema) to avoid races.
- Only persist composite filters when the user explicitly requests saving, or when a UI flow intends to save them; default behavior should be ephemeral (no DB writes).
- Validate and sanitize extracted input/output filter content (no path traversal, reasonable pattern size, reject complex regex unless explicitly allowed).
- Add debug logging around filter resolution for observability.


End-to-end implementation (two filters → persisted composite → _meta → plugin fetch)
-----------------------------------------------------------------------
This repository now uses a single durable flow that handles the user-requested input filter and output filter together and makes the persisted id available to the plugin at execution time without changing plugin TaskSchemas.

Flow summary:
1. User triggers smart-analyze or selects a tool and the Granite model returns one or more `tool_call` objects.
2. Prompt-processing resolves any inline `file_filter` (input file list) and `output_filter` (pattern files) referenced by the tool call. If the user has requested to save them (UI "Save filters" checkbox) or the orchestration policy dictates, the helper will call `file_filter_store.create_composite_filter(paths, patterns, ...)` and receive a single `filterId`.
3. When the form is rendered, the `filterId` (if resolved) is attached into the form submission payload using the `_meta` container inside `parameters`:
   - request_body.parameters['_meta']['filterId'] = "<FILTER_ID>"
   - This is done in the form submit wrapper so normal TaskSchema and form inputs remain unchanged.
4. The orchestrator packages the request and performs the FastAPI POST to run the plugin. The POST body carries `parameters._meta.filterId` as part of the request payload.
5. The plugin receives the request. At startup it looks for the `_meta.filterId` location in `parameters` (or legacy `parameters['filterId']`) and, if present, calls `file_filter_store.load_filter(filterId)` to fetch persisted `paths_json` and `patterns_json`.
6. The plugin uses the loaded `paths_json` (resolved against the provided `input_dir`) as the input file list and `patterns_json` as output filters; if absent, it falls back to inline files or directory listing logic.
7. The job is created/persisted with `jobs.filterId` set so the association is auditable and recoverable by job-runner or UI history.

Design benefits
- No per-plugin TaskSchema changes are required: `_meta` isolates system metadata from user-visible parameters.
- Works for background jobs and FastAPI POSTs because `_meta` is embedded in the POST payload.
- Keeps UI clean: users don't see `filterId` as a form field; they only see explicit "Save filters" controls when desired.

Security and validation
- Plugins MUST verify ownership/visibility of a loaded `filterId` before using it (match `owner_id` / session where applicable).
- The orchestrator should only attach persistent `filterId` values that have been validated/resolved via `process_prompt_for_filters`.
- Avoid trusting arbitrary `filterId` values from clients; prefer the server to generate and persist composite filters and then include the id in `_meta`.

Implementation checklist
- Add/create composite filter when user requests saving (already implemented in `file_filter_store.create_composite_filter`).
- Form submit wrapper injects `_meta.filterId` (implemented in `frontend/pages/chatbot/chatbot_forms.py`).
- `JobDB.create_job` extracts `_meta.filterId` and persists it to `jobs.filterId` (implemented).
- Plugin code reads `parameters['_meta']['filterId']` and calls `file_filter_store.load_filter(filterId)` (example in `src/image-summary/image_summary/main.py`).
- Integration tests exercise the full flow (added test demonstrating job stores `filterId`).

Notes
- This approach is intentionally conservative: persisted filter creation requires an explicit save action or orchestration policy, while default prompt-resolution keeps filters ephemeral unless requested.
- If you prefer storing a short-lived session mapping instead, that can be added as an additional convenience layer, but it must not replace the `_meta` POST mechanism for background-safe behavior.


Revision history
----------------
- 2026-03-09: Initial design saved by assistant.

