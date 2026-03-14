## Filter Feature Design — Simplified Two-Step Flow

Purpose
- Minimal, safe feature to support filtering between chained tools:
  1. Filter-1: consume `age-gender` output and produce a concrete list of file paths that match a simple age/gender constraint.
  2. Filter-2: accept an input directory plus an explicit subset list (file_list) and run the downstream tool only on that subset.

Principles
- Keep behavior explicit and data-first: filters produce concrete file lists (CSV/list) used directly by downstream tools.  
- Minimal parsing: support only simple filter tokens mapped to `{key, op, val}`.  
- Require user confirmation before applying filters in a multi-step chain.

Components and Responsibilities
- Prompt parser (lightweight): extract bracketed filter tokens from user prompt (e.g., `[filter: age is teenager]`) → produce `{key, op, val}`.  
- Filter utils (pure helpers): `apply_structured_filter(records, filter_spec) -> subset_files` and `filter_preview(records, filter_spec) -> {count, sample}`.  
- Orchestrator wiring: after upstream tool returns metadata, call filter utils, display preview UI, and—on user approval—pass `file_list` to downstream job request.  
- Confirmation UI: small inline preview card with `[Apply] [Edit] [Ignore]`.  
- Persistence: save applied `filter_spec` and `subset_files_count` and optionally `subset_files` into job metadata for reproducibility.

Data contract
- Structured filter:
  - { key: string, op: one-of("==", ">", "<", "in"), val: string }
  - Stored with origin and human_text for auditing: `{key,op,val,origin,human_text}`.
- Downstream invocation:
  - Prefer `file_list: List[str]` in the job request payload; fallback `file_filter: str` only when explicit list is infeasible.

Orchestration behavior
- If upstream tool returns per-file metadata (records with file_path and fields), apply filter locally to compute `subset_files`.  
- If `subset_files`  pass as explicit list.
- If no preview acceptance, run downstream tool on full input directory.

UI/UX
- Inline preview after upstream step: show count + sample (e.g., "42 files — preview: a.jpg, b.jpg, c.jpg") and actions: Apply/Edit/Ignore.  
- Badge in chat when a filter is active; allow quick remove/edit.  
- Dialog option: view full list and open job details after result is produced.

Safety, validation & limits
- Do not `eval` user input. Use controlled translation of human ops: {is -> ==, above -> >, below -> <, has -> in}.  
- Sanity cap: if subset > threshold (e.g., 10k), prompt user to confirm background run or adjust filter.  
- If filter yields zero matches, show friendly guidance and allow editing.

Testing & rollout
- Unit tests: parser, `apply_structured_filter` with representative records.  
- Integration tests: chain simulation (age-gender → preview → Apply → downstream receives `file_list`).  
- Feature flagging: gate behavior behind `FILTER_ENABLED`, default off for cautious rollout.  
- Observability: log parse result, preview_count, user decision, and persist to job metadata.

Incremental implementation steps (low-risk)
1. Add `filter_utils` helpers + unit tests.  
2. Wire orchestrator to call helpers and pass `file_list` when confirmed.  
3. Add minimal `filter_confirmation_card` UI and hook into chat rendering.  
4. Persist metadata and add integration tests.  
5. Enable feature flag in staging, verify, then roll out.

Notes
- This design focuses on minimal changes and backward compatibility: if the filter is not applied, existing flows remain unchanged.

### JSON Schema for `filter_spec`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FilterSpec",
  "type": "object",
  "description": "Structured representation of a simple filter extracted from user prompt",
  "properties": {
    "key": {
      "type": "string",
      "description": "Field name to filter on (e.g., 'age', 'gender', 'file_name')"
    },
    "op": {
      "type": "string",
      "enum": ["==", ">", "<", "in"],
      "description": "Operator for comparison (limited set for safety)"
    },
    "val": {
      "type": "string",
      "description": "Value to compare against (e.g., 'teenager', 'female', '0-2')"
    },
    "origin": {
      "type": "string",
      "enum": ["user", "llm"],
      "description": "Where the filter came from"
    },
    "human_text": {
      "type": "string",
      "description": "Original human-readable filter text (for display/audit)"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO timestamp when the filter was created"
    }
  },
  "required": ["key", "op", "val"],
  "additionalProperties": false,
  "examples": [
    {
      "key": "age",
      "op": "==",
      "val": "teenager",
      "origin": "user",
      "human_text": "[filter: age is teenager]",
      "created_at": "2026-02-05T17:00:00Z"
    },
    {
      "key": "gender",
      "op": "==",
      "val": "female",
      "origin": "llm",
      "human_text": "[only: gender=='female']",
      "created_at": "2026-02-05T17:05:00Z"
    }
  ]
}
```

### Example `job.metadata` schema (where filter info is stored)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "JobMetadata",
  "type": "object",
  "description": "Additional metadata stored with job records (optional).",
  "properties": {
    "applied_filter": {
      "$ref": "#/definitions/FilterSpec",
      "description": "The structured filter that was applied for this job (if any)."
    },
    "subset_files_count": {
      "type": "integer",
      "description": "Number of files in the computed subset (after applying the filter)."
    },
    "subset_sample": {
      "type": "array",
      "items": { "type": "string" },
      "description": "A small sample list of file paths matching the filter (for preview/debug)."
    },
    "filter_applied_by_user": {
      "type": "boolean",
      "description": "Whether the user explicitly confirmed applying the filter."
    },
    "filter_created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp when the filter was created."
    }
  },
  "additionalProperties": true,
  "definitions": {
    "FilterSpec": {
      "type": "object",
      "properties": {
        "key": { "type": "string" },
        "op": { "type": "string", "enum": ["==", ">", "<", "in"] },
        "val": { "type": "string" },
        "origin": { "type": "string", "enum": ["user", "llm"] },
        "human_text": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" }
      },
      "required": ["key", "op", "val"],
      "additionalProperties": false
    }
  }
}
```

Example usage (in job record):

```json
{
  "uid": "JOB_10",
  "status": "Completed",
  "metadata": {
    "applied_filter": {
      "key": "age",
      "op": "==",
      "val": "teenager",
      "origin": "user",
      "human_text": "[filter: age is teenager]",
      "created_at": "2026-02-05T17:00:00Z"
    },
    "subset_files_count": 42,
    "subset_sample": [
      "/data/img_001.jpg",
      "/data/img_017.jpg",
      "/data/img_023.jpg"
    ],
    "filter_applied_by_user": true,
    "filter_created_at": "2026-02-05T17:00:00Z"
  }
}
```

Here are the specific files and method-level changes you’d add/update for the three smallest changes (helper + propagation + confirmation UI). 

Change 1 — Filter‑1 executor (produce concrete subset list)

New file
frontend/pages/chatbot/utils/filter_utils.py
apply_structured_filter(records: List[Dict], filter_spec: Dict) -> List[str]
Accepts age‑gender records (each record must include file path + metadata), applies the simple predicate and returns a list of matching file paths.

filter_preview(records: List[Dict], filter_spec: Dict, sample_size: int = 10) -> Dict
Returns { count:int, sample: List[str] } for UI preview and metric storage.

Updates (call sites)

frontend/pages/chatbot/utils/job_submission_orchestrator.py
_execute_job(...) (or the inner _do_submit continuation) — after upstream tool returns metadata, call apply_structured_filter and attach subset_files/preview to the job flow / metadata.


Change 2 — Pass explicit file_list to downstream tools (Filter‑2)
Updates
frontend/pages/chatbot/utils/job_submission_orchestrator.py
_execute_job(...) / _do_submit() — when submitting the downstream job, add file_list (if present) into the request_dict payload sent to the API.
_handle_success(...) — persist subset_files into job.metadata for reproducibility.

frontend/chatbot/api_helpers.py (or frontend/api_client.py if you centralize)

post_job(api_client, http_client, config, api_endpoint: str, request_dict: Dict[str, Any]) — ensure the helper transmits arbitrary request_dict fields (no change if generic), document support for file_list and file_filter.

(Optional) frontend/chatbot/tool_config.py / tool schemas
Update the tool schema for downstream tools (e.g., ImageSummarize) to document/accept optional file_list: List[str] or file_filter: str.


Change 3 — Minimal confirmation UI (preview + Apply/Edit/Ignore)
New file (UI component)
frontend/components/chat/filter_confirmation_card.py
render_filter_confirmation_card(container, filter_spec: Dict, preview: Dict, on_apply: Callable, on_edit: Callable, on_ignore: Callable)
Renders preview count/sample and three buttons; on_apply callback receives subset_files.
Updates (integration)
frontend/pages/chatbot/utils/message_service.py

render_message_in_chat(...) (tool_result path) — when a tool result includes filter metadata/preview, call render_filter_confirmation_card to display preview inline in chat.

frontend/pages/chatbot/utils/job_submission_orchestrator.py
Add a small flow hook / callback receiver to accept the user choice from the confirmation card:

await show_filter_confirmation_and_get_choice(filter_spec, preview) (logical helper; implemented by orchestration code to wait for user's action)

Based on the returned choice, either attach file_list and continue to downstream submission or skip applying the filter.

Cross-cutting metadata & persistence

frontend/pages/chatbot/utils/message_service.py

create_chat_message_from_record(record) — ensure message.metadata includes job_id and applied_filter if present (already touched in prior edits).

frontend/pages/chatbot/utils/database_service.py or frontend/database/job_db.py

Ensure create_and_track_job / complete_job persist job.metadata.filter and job.metadata.subset_files (or response.metadata) so the applied subset is stored with the job.