# Results (UI)

## Data model

Backend returns **`ResponseBody`** (`rb.api.models`) with a discriminated **`root`**: text, markdown, file(s), directory, batch variants.

## Rendering

- **Facade:** `results_renderers.py` re-exports.
- **Modules:** `file_renderers.py`, `directory_renderers.py`, `text_renderers.py`, `table_helpers.py`, **`results_preview.py`**, **`dispatcher.py`**.

## Wiring

After submit, **`job_submission_orchestrator`** and **`result_processor`** call **`show_results`** with the **`ResponseBody`** and optional **`job_id`**.

## Chat vs jobs page

- **Chat:** results inline in the conversation column.
- **Job detail:** loads stored **`response`** JSON from **`JobDB`**.
