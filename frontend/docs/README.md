# Frontend Documentation Guides

This folder contains focused technical guides for the RescueBox NiceGUI frontend. For a high-level overview and quickstart, see the main [Frontend Guide](../readme.md).

### Documentation Guides:

1. **[ui-flow.md](./ui-flow.md)** — User flow logic from application startup to common journeys.
2. **[pages-architecture.md](./pages-architecture.md)** — Presentation layer guide for all route views in `frontend/pages/`.
3. **[chatbot-architecture.md](./chatbot-architecture.md)** — Architectural division between domain logic (`frontend/chatbot/`) and presentation (`frontend/pages/chatbot/`).
4. **[style-theme.md](./style-theme.md)** — Styling guidelines, design tokens, and theme settings.
5. **[refactor-items.md](./refactor-items.md)** — Comprehensive refactor backlog with completed milestones and upcoming slices.

## One-screen overview

- **Frontend app:** `frontend/main.py` (NiceGUI route bootstrap).
- **Chat flow:** `pages/chatbot/*` + `chatbot/*` (message handling, schema fetch, submit).
- **Results and forms UI:** `components/results/`, `components/forms/`.
- **Data:** `frontend/data/jobs.db` and `frontend/data/cache.db`.

For implementation behavior details, use code references from `ui-flow.md`.

## Python classes by file (frontend runtime)

This is a concise inventory of classes defined in `frontend/` application code (tests excluded).

| File | Classes | Functionality |
|------|---------|---------------|
| `frontend/design_tokens.py` | `Design` | Central design tokens: brand colors, typography, spacing, and styling constants. |
| `frontend/api_client.py` | `ApiClient` | Async HTTP client for communicating with RescueBox FastAPI backend endpoints. |
| `frontend/utils/backend.py` | `_BackendAvailability` | Tracks backend service connectivity and cached model availability. |
| `frontend/utils/logging.py` | `ContextFilter` | Enriches application log records with active context (client ID, conversation ID). |
| `frontend/utils/job_progress.py` | `JobProgressPoller` | Background poller syncing per-job progress SQLite files into `jobs.db` status text. |
| `frontend/pages/chatbot/chat_page.py` | `ChatbotPage` | Main `/chatbot` controller managing page layout, UI events, and tool reruns. |
| `frontend/pages/chatbot/ui_builder.py` | `FormConfig`, `ChatUIBuilder` | `FormConfig`: form config holder.<br>`ChatUIBuilder`: builds chat DOM elements (header, scroll area, inputs). |
| `frontend/pages/chatbot/state.py` | `MessageRole`, `ChatMessage`, `ChatbotStateManager`, `MessageSendParams` | `MessageRole` / `ChatMessage` / `MessageSendParams`: chat data models.<br>`ChatbotStateManager`: reactive UI state manager. |
| `frontend/pages/chatbot/message_flow_coordinator.py` | `MessageFlowCoordinator` | Orchestrates message sending, UI status updates, persistence, and result routing. |
| `frontend/chatbot/message_handler.py` | `MessageHandler` | Routes messages (slash commands vs. Granite LLM smart analyze) and filters prompts. |
| `frontend/chatbot/core.py` | `ChatbotCore` | Core client interfacing with Granite LLM calls and tool schema retrieval. |
| `frontend/chatbot/config.py` | `ChatbotConfig`, `ToolRegistry` | `ChatbotConfig`: runtime settings.<br>`ToolRegistry`: catalog of forensic tools, schemas, and slash commands. |
| `frontend/chatbot/tool_config.py` | `TextSummarize`, `ImageSummarize`, `AudioTranscribe`, `AgeGenderPredict`, `FaceFindBulk`, `FaceBulkUpload`, `DeepfakeDetection`, `FileSystemScan`, `UfdrMount`, `TextSearch`, `ImageSearch`, `ImageSeriesSearch`, `RescueBoxToolCall`, `ToolCallList` | Pydantic schema models defining parameters and structured tool call specifications. |
| `frontend/chatbot/multi_tool/models.py` | `MultiToolCallResult` | Model representing sequenced multi-tool execution chains and dependencies. |
| `frontend/pages/chatbot/ui_delegate.py` | `ChatUIDelegate` | Protocol isolating UI rendering (messages, status, errors) from flow coordination. |
| `frontend/pages/chatbot/pickers.py` | `ToolPicker`, `AnalysisPicker` | Modal dialogs for interactive browsing and selection of tools and workflows. |
| `frontend/pages/chatbot/form_submit_handler.py` | `FormSubmitHandler` | Handles form validation, case note dialogs, and job submission execution. |
| `frontend/pages/chatbot/result_processor.py` | `ResultProcessor` | Renders model responses onto the UI as chat bubbles, error notices, or tool forms. |
| `frontend/pages/chatbot/database_service.py` | `DatabaseService` | Bridges UI state to SQLite chat history and job database records. |
| `frontend/pages/chatbot/handlers/base.py` | `BaseHandler`, `FormErrorHandler` | Base event handling contracts and form error display helpers. |
| `frontend/pages/chatbot/handlers/job_submit_params.py` | `JobSubmitParams` | Dataclass bundling parameters, schemas, and callbacks for job submissions. |
| `frontend/pages/chatbot/handlers/job_lifecycle_service.py` | `JobLifecycleService` | Manages job records across creation, execution, and failure lifecycles. |
| `frontend/pages/chatbot/handlers/job_orchestrator.py` | `JobSubmissionOrchestrator` | Orchestrates background job submission, status polling, and results rendering. |
| `frontend/pages/chatbot/handlers/pipeline.py` | `PipelineHandler` | Coordinates multi-step tool execution pipelines with automatic path injection. |
| `frontend/pages/chatbot/handlers/pipeline_planner.py` | `NextPipelineStepPlan` | Computes execution plans and path chaining between consecutive pipeline steps. |
| `frontend/components/forms/form_generator.py` | `FormGenerator` | Dynamically builds NiceGUI form controls based on OpenAPI tool schemas. |
| `frontend/components/results/dispatch.py` | `ResultDispatcher`, `ResultsPreview` | `ResultDispatcher`: dispatches results to specialized renderers.<br>`ResultsPreview`: preview container. |
| `frontend/components/results/image_summary.py` | `_ImageSummaryCssState` | Manages CSS injection and styling state for image summary rendering. |
| `frontend/components/results/serve_paths.py` | `_ServeRouteState` | Manages local media file serving routes for result preview display. |
| `frontend/components/chat/ui_operations.py` | `UIOperations` | Safe UI helpers for scroll actions, notifications, and client DOM operations. |
| `frontend/components/shared/stepper.py` | `WorkflowStepper` | Step-by-step progress indicator widget for pipeline walkthroughs. |
| `frontend/components/demo.py` | `WalkthroughPreset` | Configuration model defining preset parameters for demo walkthroughs. |
| `frontend/pages/logs.py` | `LogsPage` | Controller for the `/logs` route featuring log level filtering and auto-refresh. |
| `frontend/pages/models.py` | `ModelsPage` | Controller for the `/models` route displaying model catalog cards and statuses. |
| `frontend/pages/jobs/list.py` | `JobsPage` | Controller for the `/jobs` route managing the jobs table and filters. |
| `frontend/database/schemas.py` | `DatabaseSchema`, `JobDatabaseSchema`, `ChatHistoryDatabaseSchema`, `SchemaManager` | Table schemas, database creation logic, and schema migration managers. |
| `frontend/database/base_db.py` | `BaseDatabase` | Base async SQLite database client providing connection pooling and transactions. |
| `frontend/database/validation.py` | `DatabaseValidator` | Validates data integrity, constraints, and schemas before database persistence. |
| `frontend/database/job_models.py` | `JobStatus`, `JobRecord` | Enum and dataclass models representing job statuses and database records. |
| `frontend/database/job_db.py` | `JobDB` | Repository for job creation, status updates, and history queries. |
| `frontend/database/case_db.py` | `CaseRecord`, `CaseDB` | Data models and repository for case management operations. |
| `frontend/database/chat_history_db.py` | `ConversationRecord`, `ChatMessageRecord`, `ChatHistoryDB` | Data models and repository for conversation history and message persistence. |
| `frontend/utils/browser.py` | `DirectoryBrowser`, `FileBrowser` | Native modal dialogs for browsing and selecting directories and files. |
