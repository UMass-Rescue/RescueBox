# Jobs (frontend)

## What counts as a job

A plugin **`POST`** with JSON `inputs` / `parameters` to a Typer-registered route (e.g. `audio/transcribe`, `ufdr_mounter/mount`).

## Lifecycle

1. **Validate** — `validators.py` → `RequestBody`.
2. **Submit** — **`JobSubmissionOrchestrator`** (`job_submission_orchestrator.py`) schedules async work; **`post_job`** + **`submit_job_orchestrator`** call the backend.
3. **Record** — **`JobDB`** (`job_db.py`) stores uid, optional `endpoint`, request/response JSON, `taskSchema`, **`JobStatus`** enum (`Running`, `Completed`, `Failed`, `Canceled`).
4. **Show** — **`show_results`** / results components.
5. **Poll** — On chat load, **`ChatbotPage._poll_job_status`** in **`chatbot.py`** reads **`job_db`** at **`POLL_INTERVAL`** from config (seconds).

## Chatbot vs legacy fields

- **Chatbot:** `endpoint` string on the job row.
- **Optional:** `modelUid` / `taskUid` for older flows.

## Pages

- **`/jobs`** — `jobs.py`
- **`/jobs/{job_id}`** — `job_details.py` (uses **`ResultsPreview`**, **`apply_saved_theme`**)

## Errors

**`httpx.HTTPStatusError`** from **`post_job`** maps status and `detail` for UI; plugins may return **400/422/503** etc.
