# case-export

Minimal **job → JSON-LD fragment** helpers for RescueBox:

1. **On job completion** — `database_service.complete_job` calls `case_export.hooks.on_job_completed`, which writes `frontend/data/case_exports/{job_uid}.jsonld` (best-effort).
2. **Export button** — Jobs → job details → **Export CASE JSON-LD** downloads the same shape for the open job.

The fragment uses UCO/CASE namespace prefixes (`uco:`, `case:`) with `uco:Tool` + `uco:Action` and embedded `rb:requestSummary` / `rb:outputSummary` / `rb:artifactPaths`. It is **not** SHACL-validated; you can add [`case-uco`](https://github.com/vulnmaster/CASE-UCO-SDK) later for stricter graphs.

## Layout

```
src/case-export/
  case_export/
    fragment.py   # build @graph from job dict
    persist.py    # bytes + write cache file
    hooks.py      # on_job_completed
```
