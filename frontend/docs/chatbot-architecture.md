# Chatbot Architecture

The RescueBox Chatbot has been refactored from a monolithic `chatbot.py` file into a modular package structure to improve maintainability, testability, and scalability.

## Package Structure

The chatbot logic is now located in `frontend/pages/chatbot/` and is split into four primary modules:

### 1. State Management (`state.py`)
- **`ChatbotStateManager`**: Centralizes all conversation and UI state.
- **`ChatMessage`**: Dataclass representing individual chat messages.
- **`MessageSendParams`**: Typed bundles for chat UI flows to reduce parameter complexity.

### 2. Message Flow Coordination (`coordinator.py`)
- **`MessageFlowCoordinator`**: The central orchestrator that unifies message processing, result routing, and form submission.
- **`MessageProcessor`**: Handles the logic for sending messages and processing initial AI responses.
- **`ResultProcessor`**: Processes structured results (tool calls, forms, pickers) from the message handler.
- **`PipelineHandler`**: Manages multi-step tool execution (e.g., Image Summary → Search).

### 3. User Interface (`ui.py`)
- **`ChatbotPage`**: The main route handler and high-level UI orchestrator.
- **`ChatUIBuilder`**: Builds the complete chat UI using reusable design tokens.
- **`MessageRenderer`**: Handles the visual rendering of different message types (user, assistant, tool calls).
- **`UIOperations`**: Utility class for JS-based UI actions like scrolling and notifications.

### 4. Logic & Event Handlers (`handlers.py`)
- **`JobSubmissionOrchestrator`**: Manages the lifecycle of a job submission from form to completion.
- **Pickers**: `ToolPicker` and `AnalysisPicker` for selecting tools and analysis modes.

URL query handling (`?load_conversation=`, `?rerun=`) lives in **`ui.py`** (`chatbot_page` and `_extract_chatbot_query_from_client`).

## Public API (`__init__.py`)

The package exposes a clean public API, maintaining backward compatibility for existing imports:

```python
from frontend.pages.chatbot import ChatbotPage, ChatbotStateManager
```


