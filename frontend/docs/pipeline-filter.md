# Pipeline and filter

## Forensic filter (implemented)

- **`ChatbotConfig.FILTER_ENABLED`** — `frontend/chatbot/config.py`.
- **`is_rescuebox_request()`** — `frontend/chatbot/utils.py`; called from **`message_handler`** for natural language and **`/analyze`** paths.
- **`get_rejection_message()`** when input is rejected.

Disable for dev: set **`FILTER_ENABLED=False`** on config or env as supported in `ChatbotConfig`.

## Slash command `/analyze`

Implemented in **`message_handler`** (analysis picker vs smart analyze); same filter hooks where applicable.

## Multi-tool chains

Sequential handling in **`multi_tool_handler.py`**. Optional file subset between steps uses **`file_filter_store`** / batch inputs where wired — inspect call sites for exact argument names.
