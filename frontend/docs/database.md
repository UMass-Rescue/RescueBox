# Database (frontend SQLite)

**Directory:** `frontend/data/` (`DATA_DIR` in `frontend/config.py`).

## Files

| File | Purpose |
|------|---------|
| **`jobs.db`** | **`JobDB`** jobs table **and** **`ChatHistoryDB`** conversation/message tables (single SQLite file) |
| **`cache.db`** | Model list cache — `init_db()` / `cache_models` in `frontend/database/__init__.py` |

Access: **`get_job_db()`**, **`get_chat_history_db()`** from `frontend.database`.

## Rows

Many queries use **`sqlite3.Row`** — use **`row["column"]`** indexing (not **`.get()`** unless converted to `dict`).

## NiceGUI storage (not SQLite)

**`app.storage.user`** / client storage — session user id, conversation id; **`nicegui_storage.py`**.
