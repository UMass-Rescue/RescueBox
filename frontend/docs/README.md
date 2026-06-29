# Frontend docs (simple set)

This folder is intentionally reduced to **3 docs**:

1. **[ui-flow.md](./ui-flow.md)** - user flow logic from startup to common journeys.
2. **[style-theme.md](./style-theme.md)** - style/theme rules and where to change UI appearance.
3. **[README.md](./README.md)** - this quick index.

Additional planning artifact:

- **[refactor-items.md](./refactor-items.md)** - comprehensive refactor backlog with priorities and PR-sized first slices.

## One-screen overview

- **Frontend app:** `frontend/main.py` (NiceGUI route bootstrap).
- **Chat flow:** `pages/chatbot/*` + `chatbot/*` (message handling, schema fetch, submit).
- **Results and forms UI:** `components/results/`, `components/forms/`.
- **Data:** `frontend/data/jobs.db` and `frontend/data/cache.db`.

For implementation behavior details, use code references from `ui-flow.md`.

## Python classes by file (frontend runtime)

This is a concise inventory of classes defined in `frontend/` application code (tests excluded).

| File | Classes |
|------|---------|
| `frontend/design_tokens.py` | `Design` |
| `frontend/api_client.py` | `ApiClient` |
| `frontend/utils/backend.py` | `_BackendAvailability` |
| `frontend/utils/logging.py` | `ContextFilter` |
| `frontend/pages/chatbot/chat_page.py` | `ChatbotPage` |
| `frontend/pages/chatbot/ui_builder.py` | `FormConfig`, `ChatUIBuilder` |
| `frontend/pages/chatbot/state.py` | `MessageRole`, `ChatMessage`, `ChatbotStateManager`, `MessageSendParams` |
| `frontend/pages/chatbot/message_flow_coordinator.py` | `MessageFlowCoordinator` |
| `frontend/pages/chatbot/message_processor.py` | `MessageProcessor` |
| `frontend/chatbot/message_handler.py` | `MessageHandler` |
| `frontend/chatbot/core.py` | `ChatbotCore` |
| `frontend/chatbot/config.py` | `ChatbotConfig`, `ToolRegistry` |
| `frontend/chatbot/tool_config.py` | `TextSummarize`, `ImageSummarize`, `AudioTranscribe`, `AgeGenderPredict`, `FaceFindBulk`, `FaceBulkUpload`, `DeepfakeDetection`, `FileSystemScan`, `UfdrMount`, `TextSearch`, `ImageSearch`, `ImageSimilaritySearch`, `RescueBoxToolCall`, `ToolCallList` |
| `frontend/chatbot/multi_tool/models.py` | `MultiToolCallResult` |
| `frontend/pages/chatbot/pickers.py` | `ToolPicker`, `AnalysisPicker` |
| `frontend/pages/chatbot/form_submit_handler.py` | `FormSubmitHandler` |
| `frontend/pages/chatbot/result_processor.py` | `ResultProcessor` |
| `frontend/pages/chatbot/database_service.py` | `DatabaseService` |
| `frontend/pages/chatbot/handlers/base.py` | `BaseHandler`, `FormErrorHandler` |
| `frontend/pages/chatbot/handlers/job_submit_params.py` | `JobSubmitParams` |
| `frontend/pages/chatbot/handlers/job_lifecycle_service.py` | `JobLifecycleService` |
| `frontend/pages/chatbot/handlers/job_orchestrator.py` | `JobSubmissionOrchestrator` |
| `frontend/pages/chatbot/handlers/pipeline.py` | `PipelineHandler` |
| `frontend/pages/chatbot/handlers/pipeline_planner.py` | `NextPipelineStepPlan` |
| `frontend/components/forms/form_generator.py` | `FormGenerator` |
| `frontend/components/results/dispatch.py` | `ResultDispatcher`, `ResultsPreview` |
| `frontend/components/results/image_summary.py` | `_ImageSummaryCssState` |
| `frontend/components/results/serve_paths.py` | `_ServeRouteState` |
| `frontend/components/chat/ui_operations.py` | `UIOperations` |
| `frontend/components/shared/stepper.py` | `WorkflowStepper` |
| `frontend/components/demo.py` | `WalkthroughPreset` |
| `frontend/components/base_component.py` | `BaseComponent`, `ComponentRegistry` |
| `frontend/pages/logs.py` | `LogsPage` |
| `frontend/pages/models.py` | `ModelsPage` |
| `frontend/pages/jobs/list.py` | `JobsPage` |
| `frontend/database/schemas.py` | `DatabaseSchema`, `JobDatabaseSchema`, `ChatHistoryDatabaseSchema`, `SchemaManager` |
| `frontend/database/base_db.py` | `BaseDatabase` |
| `frontend/database/validation.py` | `DatabaseValidator` |
| `frontend/database/job_models.py` | `JobStatus`, `JobRecord` |
| `frontend/database/job_db.py` | `JobDB` |
| `frontend/database/case_db.py` | `CaseRecord`, `CaseDB` |
| `frontend/database/chat_history_db.py` | `ConversationRecord`, `ChatMessageRecord`, `ChatHistoryDB` |
| `frontend/utils/browser.py` | `DirectoryBrowser`, `FileBrowser` |
