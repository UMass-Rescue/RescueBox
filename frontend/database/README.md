# Frontend database package

## What’s in the repo

| Module | Role |
|--------|------|
| **`job_db.py`** | **`JobDB`** — job rows (`uid`, optional `endpoint` / `modelUid` / `taskUid`, request/response JSON, `taskSchema`, **`JobStatus`**) |
| **`chat_history_db.py`** | **`ChatHistoryDB`** — conversations + chat messages |
| **`base_db.py`**, **`schemas.py`**, **`validation.py`** | Shared SQLite helpers for chat history |
| **`__init__.py`** | **`cache.db`** — model list cache (`cache_models`, `get_cached_models`); **`init_db()`** for cache schema |

## File on disk

- **`frontend/data/jobs.db`** — **both** job records **and** chat history tables (see `ChatHistoryDB.__init__` passing `"jobs.db"`).
- **`frontend/data/cache.db`** — cached **`GET /api/models`** (or equivalent) payload for faster UI.

## Usage

```python
from frontend.database import get_job_db, get_chat_history_db

job_db = get_job_db()
chat_db = get_chat_history_db()
```

Jobs created from the chatbot flow are written in **`job_submission_orchestrator.py`**; chat messages in **`chat_history_db`** / **`DatabaseService`** patterns.

## Documentation

Canonical overview: **`../docs/README.md`** and **`../docs/database.md`**.
