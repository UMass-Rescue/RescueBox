# Chat Components & Jobs Pages Architecture (Modular Refactor 2026)

This document describes the modular architecture of the chat UI components and the jobs management pages.

## Chat Components (`frontend/components/chat/`)

The chat package provides the fundamental UI building blocks for the assistant interface.

| Module | Description |
| :--- | :--- |
| `rendering.py` | Core renderers for user/assistant message bubbles and conversation list cards. |
| `ui_elements.py` | Structural components including the top toolbar, messages scroll area, and the message composer (input area). |
| `dialogs.py` | Modal windows for help text, conversation history browsing, and detailed message inspection. |
| `utils.py` | Low-level `UIOperations` for JavaScript-based scrolling/navigation. |

---

## Jobs Pages (`frontend/pages/jobs/`)

The jobs package manages the full lifecycle and display of forensic tasks.

| Module | Description |
| :--- | :--- |
| `list.py` | Implementation of the `/jobs` index page. Handles polling, sorting, and pipeline grouping. |
| `details.py` | Implementation of the `/jobs/{id}` view. Orchestrates output previews, input summaries, and metadata displays. |
| `components.py` | Specialized job UI such as audit trail export buttons and result action buttons. |
| `utils.py` | Backend-facing logic for partitioning jobs into pipelines and extracting fields from database records. |

### Public API
Both packages use an `__init__.py` facade to export their primary page handlers and components, allowing the rest of the application to use them without deep-linking into the internal file structure.
