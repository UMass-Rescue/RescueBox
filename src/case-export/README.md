# case-export

Minimal **job → JSON-LD fragment** helpers for RescueBox:

1. **On job completion** — `database_service.complete_job` calls `case_export.hooks.on_job_completed`, which writes `frontend/data/case_exports/{job_uid}.jsonld` (best-effort).
2. **Export button** — Jobs → job details → **Export CASE JSON-LD** downloads the same shape for the open job.

Exports use the Python [`case-uco`](https://github.com/vulnmaster/CASE-UCO-SDK) `CASEGraph` (typed `InvestigativeAction`, `ProvenanceRecord`, `File`/`Directory`, etc.) plus `rb:requestSummary` / `rb:outputSummary` / `rb:artifactPaths` on the action node. Optional SHACL: `poetry install --with case-validation` then `validate_fragment_jsonld(doc)` (runs `case_validate` when on `PATH`).

## Layout

```
src/case-export/
  case_export/
    fragment.py   # build @graph from job dict
    persist.py    # bytes + write cache file
    hooks.py      # on_job_completed
```
