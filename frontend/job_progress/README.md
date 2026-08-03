# Job progress (frontend)

Per-job SQLite files under ``RESCUEBOX_PROGRESS_DIR`` (default: ``data/progress/{job_id}.db``).

- **init_job_progress** — called when a tracked job starts.
- **JobProgressPoller** — every 10s, reads percent and sets ``jobs.statusText`` to ``Running`` or ``N% done``.
- **cleanup_job_progress** — deletes the job's progress file when the API call finishes.

Backend plugins report via ``rb.lib.job_progress`` (see ``rb/lib/job_progress.py``).
The API receives ``X-RescueBox-Job-Id`` on job POST requests.
