# Backend plugin output contract (TODO for plugin authors)

This document describes a **recommended, shared shape** for plugin responses so **pipelines**, **the RescueBox UI**, and the **per-job pipeline index** (`pipeline_io_links` on the frontend) can trace **which input file produced which output** and attach **metadata** per row.

Implementation status: **partial** — image summary already emits `file_pairs`; other plugins should converge on this contract.

---

## Goals

1. **Downstream steps** can chain without inferring paths from filenames alone.
2. **Any** step can be recorded as **input path → output path → metadata** for later joins (summarize, search, image search, age–gender, etc.).
3. **One consistent pattern** across Python types (`rb.lib.plugin_io`) and JSON payloads.

---

## Contract: one row per produced artifact

For each **output artifact** (file) the plugin creates or selects as a primary result row, the plugin should expose:

| Field | Required | Meaning |
|--------|----------|---------|
| **input_path** | Yes | Absolute (or stable) path to the **source** file or primary input this row depends on. |
| **output_path** | Yes | Absolute (or stable) path to the **artifact** for this row (file the next step or UI will reference). |
| **metadata** | Yes | JSON-serializable **object** (k=v): scores, bbox, model name, plugin id, face id, etc. Use `{}` if nothing extra. |

### Python (`rb.lib.plugin_io`)

- **`InputOutputFilePair`** — `input_path` + `output_path` only (minimal pair).
- For rows that need metadata, use a **dict** or a future TypedDict (see TODO below) with keys `input_path`, `output_path`, `metadata`.

### JSON (e.g. inside `TextResponse.value`)

Plugins that already return structured JSON should add:

- **`file_pair_rows`** (recommended name): array of  
  `{ "input_path": "...", "output_path": "...", "metadata": { ... } }`  
  Same length as logical outputs; **metadata** may be `{}`.

**Backward compatibility:** plugins may keep **`file_pairs`** as a list of `{ "input_path", "output_path" }` only; indexers can treat missing **metadata** as `{}`.

---

## TODO checklist (backend plugins)

- [ ] **Emit provenance rows** for every primary output file: **input_path**, **output_path**, and **metadata** (object, possibly empty).
- [ ] **Normalize paths** where possible (e.g. `Path.resolve()`), consistent with the rest of the job.
- [ ] **Document** in the plugin’s `app-info.md` how **input_path** is chosen when multiple inputs map to one output (or one input to many outputs).
- [ ] **Avoid huge payloads**: cap list size or strip large blobs from **metadata**; do not embed multi‑MB content in JSON.
- [ ] **Optional:** add **`plugin`** / **`endpoint`** inside **metadata** for easier filtering in pipelines.

### Plugins with special shapes

- **No file outputs:** either omit **file_pair_rows** or document why; non-file results may use synthetic keys in **metadata** only if the pipeline agrees.
- **One input → many outputs:** multiple rows; **input_path** may repeat; **output_path** must be unique per row where the index expects a unique **output_path**.

---

## Relationship to the frontend pipeline index

The chat UI can call **`insert_pipeline_io_links`** with rows `{ input_path, output_path, metadata }` after a job completes (per user + **pipeline root job id**). That requires either:

- A **generic recorder** that parses **`file_pair_rows`** from any plugin response shape, or  
- **Per-plugin recorders** (as today for image summary) until a generic path exists.

---

## References (code)

- `src/rb-lib/rb/lib/plugin_io.py` — `InputOutputFilePair`, `ImageSummaryFilePair` alias.
- `frontend/database/pipeline_job_index_db.py` — `pipeline_io_links` table and `insert_pipeline_io_links`.
- Image summary: `src/image-summary/image_summary/main.py` — `file_pairs` in JSON payload.

---

## Follow-ups (repository TODO)

- [ ] Add **`FilePairWithMetadata`** TypedDict in `rb.lib.plugin_io` (`input_path`, `output_path`, `metadata: dict`).
- [ ] Generic **frontend** hook: parse **`file_pair_rows`** from responses for any endpoint and call **`insert_pipeline_io_links`**.
- [ ] Align **image search** / **text search** plugins to emit **`file_pair_rows`** (or equivalent) and document scoring fields in **metadata**.
