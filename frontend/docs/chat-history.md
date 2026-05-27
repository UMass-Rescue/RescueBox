# Chat history

## Purpose

Persist conversations in **SQLite** (`jobs.db`, chat tables) so users can reopen threads and **re-run** tool calls with stored arguments.

## Implementation

- **Data layer:** **`ChatHistoryDB`** — `frontend/database/chat_history_db.py` (same DB file as jobs: **`frontend/data/jobs.db`** via `BaseDatabase`).
- **UI:**  `DatabaseService.ensure_active_conversation(self.state_manager)`.
- **Session:** `frontend/utils/nicegui_storage.py` — current conversation id, load/rerun hints.
- **URL:** `frontend/pages/chatbot/ui.py` (`chatbot_page`) — `?load_conversation=`, `?rerun=`.

## Schema (conceptual)

- **conversations** — id, title, timestamps, message count, metadata.
- **chat_messages** — id, conversation_id, role, content, `message_type` (`text`, `tool_call`, `tool_result`, `error`), tool columns, `metadata` JSON.


