# UI & User Usage Flow Architecture

Comprehensive reference for user journeys, execution flows, and corresponding code handlers across RescueBox Desktop frontend.

---

## 1. Application Runtime Bootstrap

### Scenario 1.1: Application Launch & Service Warmup
- **User Action:** User launches RescueBox Desktop (`poetry run python -m frontend.main` or via installer executable).
- **Runtime Journey:**
  1. Startup configuration and environment variables are loaded (`frontend/config.py`).
  2. Database initialization runs: `JobDB`, `CaseDB`, `ChatHistoryDB`, and model cache SQLite files are prepared in `frontend/data/`.
  3. Dynamic page routes are registered via NiceGUI decorators (`frontend/pages/__init__.py`).
  4. Asynchronous model prefetching occurs (`prefetch_and_cache_models()` queries `/api/models` and caches definitions into `cache.db`).
  5. UI server starts listening on `APP_PORT` with configured theme preference and browser visibility.
- **Code Handlers:**
  - `frontend/main.py`: `init_db()`, `prefetch_and_cache_models()`, `ui.run()`
  - `frontend/database/job_db.py`: `init_database()`, `_initialize_schema_sync()`
  - `frontend/database/chat_history_db.py`: `init_database()`, `ChatHistoryDB._create_schema()`
  - `frontend/database/case_db.py`: `init_database()`, `CaseDB._create_schema()`
  - `frontend/database/model_cache.py`: `init_db()`, `cache_models()`
  - `frontend/api_client.py`: `ApiClient.get("/models")`

---

## 2. Case Management Workflows

### Scenario 2.1: Case Creation & Activation
- **User Action:** On `/` (Dashboard) or `/case`, user enters a case name, investigator ID, and optional directory root, then clicks "Create Case".
- **Runtime Journey:**
  1. Input is validated for non-empty case title and path structure.
  2. `CaseDB.create_case()` records the case with a unique ID into `jobs.db` (`cases` table).
  3. `set_active_case_id()` stores the newly created case ID into session state (`app.storage.user["active_case_id"]`).
  4. Active case metadata is broadcast to UI layout and navbar components.
- **Code Handlers:**
  - `frontend/pages/home.py`, `frontend/pages/home_dashboard.py`: Dashboard view & case forms.
  - `frontend/pages/home_case_overview.py`: Detailed case statistics and recent activity.
  - `frontend/database/case_db.py`: `CaseDB.create_case()`, `CaseDB.get_case_by_id()`
  - `frontend/utils/storage.py`: `set_active_case_id()`, `get_active_case_id()`, `get_active_case_record()`
  - `frontend/components/shared/breadcrumbs.py`: Dynamic case indicator in header.

### Scenario 2.2: Switching Active Case
- **User Action:** User selects an existing case from the case dropdown or list.
- **Runtime Journey:**
  1. `set_active_case_id(new_case_id)` updates session storage.
  2. Subsequent chat sessions, job submissions, and job filters are scoped to this `active_case_id`.
- **Code Handlers:**
  - `frontend/pages/home_case_overview.py`: Case switcher dialog/table.
  - `frontend/utils/storage.py`: `set_active_case_id()`

---

## 3. Chat & Natural Language Tool Selection

### Scenario 3.1: Natural Language Analysis (Smart Analyze)
- **User Action:** In `/chatbot`, user types a prompt (e.g., *"Find all faces in directory D:/evidence/photos"* or *"Transcribe audio recording.wav"*).
- **Runtime Journey:**
  1. Message input triggers `ChatbotPage._handle_send_message()`.
  2. Delegated to `MessageFlowCoordinator.process_user_message()`.
  3. `MessageFlowCoordinator` records the user message and routes to `MessageHandler.handle_message()`.
  4. `MessageHandler` checks for slash commands; finding none, routes to `MessageHandler.handle_smart_analyze()`.
  5. `MessageHandler` builds system prompts with dynamic tool schemas from `ToolRegistry` (`frontend/chatbot/tool_config.py`).
  6. `ChatbotCore.call_granite_model()` queries Ollama / IBM Granite LLM.
  7. The LLM response is parsed into `RescueBoxToolCall` or `MultiToolCallResult`.
  8. If single tool call: returns a `show_form` intent. If multi-tool call: returns a `multi_tool_flow` intent.
  9. Result is handed to `ResultProcessor.process_result()` to render the tool's form.
- **Code Handlers:**
  - `frontend/pages/chatbot/chat_page.py`: `ChatbotPage._handle_send_message()`
  - `frontend/pages/chatbot/ui_delegate.py`: `ChatUIDelegate` (isolates UI notifications and message bubble rendering)
  - `frontend/pages/chatbot/message_flow_coordinator.py`: `MessageFlowCoordinator.process_user_message()`
  - `frontend/chatbot/message_handler.py`: `MessageHandler.handle_smart_analyze()`
  - `frontend/chatbot/core.py`: `ChatbotCore.call_granite_model()`
  - `frontend/chatbot/tool_config.py`: `ToolCallList`, `RescueBoxToolCall`, schema definitions
  - `frontend/pages/chatbot/result_processor.py`: `ResultProcessor.process_result()`

### Scenario 3.2: Direct Slash Command Execution
- **User Action:** User types `/transcribe`, `/faces`, `/summarize`, or `/help` into chat.
- **Runtime Journey:**
  1. Looks up the command in `ToolRegistry.get_slash_commands()`.
  2. Formulates a `show_form` action targeting the mapped endpoint (e.g. `/audio/transcribe`).
  3. If user provided inline arguments (e.g. `/transcribe path="test.wav"`), arguments are parsed.
  4. Dispatches to `ResultProcessor.process_result()`.
- **Code Handlers:**
  - `frontend/chatbot/message_handler.py`: `_extract_slash_command()`, `_parse_slash_arguments()`
  - `frontend/chatbot/config.py`: `ToolRegistry`

### Scenario 3.3: Interactive Tool & Analysis Pickers
- **User Action:** User clicks the "Tools" or "Workflows" button in the chat interface.
- **Runtime Journey:**
  1. `ToolPicker` or `AnalysisPicker` renders a modal dialog with categorized tools and workflow templates.
  2. User clicks a tool card; picker invokes callback with the selected endpoint and default arguments.
  3. Invokes `load_and_show_form()` directly into the chat container.
- **Code Handlers:**
  - `frontend/pages/chatbot/pickers.py`: `ToolPicker.show()`, `AnalysisPicker.show()`
  - `frontend/components/chat/dialogs.py`: Dialog wrapper utilities

---

## 4. Dynamic Form Generation & Autofill

### Scenario 4.1: Task Schema Fetching & Field Rendering
- **User Action:** Tool is selected; form appears in the chat stream.
- **Runtime Journey:**
  1. `load_and_show_form()` is called with endpoint and initial values.
  2. Fetches OpenAPI parameter specifications via `ChatbotCore.get_task_schema_from_endpoint()`.
  3. `inject_pipeline_path()` inspects prior job outputs and automatically populates input path fields if part of a pipeline.
  4. `autofill` utilities inject default case directory paths for output directories or UFDR mount targets.
  5. `FormGenerator.generate_form()` iterates through schema properties and instantiates field components:
     - Directory picker: `browse_directory_simple`
     - File picker: `browse_file_simple`
     - Sliders, dropdowns, text inputs, toggles
  6. Submits form via `FormSubmitHandler.submit_form()`.
- **Code Handlers:**
  - `frontend/pages/chatbot/ui_flow.py`: `load_and_show_form()`
  - `frontend/chatbot/core.py`: `ChatbotCore.get_task_schema_from_endpoint()`
  - `frontend/chatbot/pipeline_context.py`: `inject_pipeline_path()`, `get_pipeline_output_path()`
  - `frontend/components/forms/field_builders.py`: Input field dispatch coordinator
  - `frontend/components/forms/path_inputs.py`: Directory and file path input widgets
  - `frontend/components/forms/parameter_fields.py`: Numeric, slider, enum, and text parameter widgets
  - `frontend/utils/browser.py`: Directory and file browser modal dialogs

---

## 5. Job Submission & Background Orchestration

### Scenario 5.1: Form Submission & Case Gating
- **User Action:** User fills parameters and clicks "Submit" / "Execute".
- **Runtime Journey:**
  1. `FormSubmitHandler.submit_form()` checks if an active case is selected (`get_active_case_id()`). If none, notifies user and aborts.
  2. Validates inputs against schema (`validate_form_data()`). For image-matching archive tasks it also checks investigation labels against the backend (`validate_image_archive_form()`).
  3. Constructs `JobSubmitParams` data object.
  4. Hands execution over to `JobSubmissionOrchestrator.submit_job()`.
- **Code Handlers:**
  - `frontend/pages/chatbot/form_submit_handler.py`: `FormSubmitHandler.submit_form()`
  - `frontend/utils/storage.py`: `get_active_case_id()`
  - `frontend/utils/validators.py`: `validate_form_data()`
  - `frontend/utils/image_archive_validation.py`: `validate_image_archive_form()`
  - `frontend/pages/chatbot/handlers/job_submit_params.py`: `JobSubmitParams`

### Scenario 5.2: Job Persistence & API Dispatch
- **User Action:** Background submission starts; loading spinner appears in chat.
- **Runtime Journey:**
  1. `JobLifecycleService.create_tracked_job()` creates a row in `jobs.db` with status `Pending` and persists request snapshot.
  2. `JobLifecycleService.record_job_started()` records a `job_started` message in `chat_history.db`.
  3. Renders loading indicator in chat (`render_loading_row()`).
  4. Dispatches HTTP POST to backend endpoint via `ChatbotCore.submit_job()` / `api_helpers.post_job()`.
  5. Initializes job progress poller (`init_job_progress()`).
  6. If submission succeeds immediately (synchronous job): completes job via `JobLifecycleService.complete_successful_submission()`.
  7. If asynchronous background task: enters polling loop (`ChatbotPage._poll_job_status()` or background execution) until status changes to `Completed` or `Failed`.
- **Code Handlers:**
  - `frontend/pages/chatbot/handlers/job_orchestrator.py`: `JobSubmissionOrchestrator._execute_job()`, `_background_submit()`
  - `frontend/pages/chatbot/chat_page.py`: `ChatbotPage._poll_job_status()`
  - `frontend/pages/chatbot/handlers/job_lifecycle_service.py`: `JobLifecycleService`
  - `frontend/database/job_db.py`: `JobDB.create_job()`, `JobDB.update_job_status()`
  - `frontend/database/chat_history_db.py`: `ChatHistoryDB.add_message()`
  - `frontend/chatbot/core.py`: `ChatbotCore.submit_job()`
  - `frontend/utils/job_progress.py`: `JobProgressPoller`, `init_job_progress()`, `cleanup_job_progress()`

---

## 6. Result Processing & Multi-Modal Rendering

### Scenario 6.1: Results Display in Chat
- **User Action:** Job finishes; results preview card appears in the chat feed.
- **Runtime Journey:**
  1. `show_results()` receives the backend response payload and job UID.
  2. Dispatches to `ResultsPreview` / `ResultDispatcher`.
  3. Automatically selects appropriate renderer based on endpoint and output keys:
     - Media / Video / Audio: `render_media_response()` (inline audio players, video thumbnails)
     - Text / Summaries / Transcripts: `render_text_response()` (markdown preview, full text modal)
     - Faces / Object Detection: `render_faces_response()` (gallery grid, confidence badges)
     - Generic / Tabular Data: `create_sortable_table()`
  4. Saves tool result message to conversation history via `DatabaseService.save_tool_result_to_history()`.
- **Code Handlers:**
  - `frontend/pages/chatbot/ui_flow.py`: `show_results()`, `_show_results_body()`
  - `frontend/components/results/dispatch.py`: `ResultDispatcher.render()`, `ResultsPreview.render()`
  - `frontend/components/results/text.py`: Markdown and text rendering coordinator
  - `frontend/components/results/text_modal.py`: Full-document text/markdown preview dialog
  - `frontend/components/results/text_search.py`: Semantic search results and searchable file list
  - `frontend/components/results/batch_text.py`: Transcription and multi-text cards
  - `frontend/components/results/table_helpers.py`: Table generation and sorting

---

## 7. Multi-Step Pipelines & Metadata Filtering

### Scenario 7.1: Chained Tool Execution
- **User Action:** User initiates a multi-stage workflow (e.g., *Scan files -> Extract faces -> Classify age/gender*).
- **Runtime Journey:**
  1. `MultiToolCallResult` holds a list of planned tool invocations.
  2. First tool executes and finishes.
  3. `JobSubmissionOrchestrator` detects `remaining_calls` and delegates to `PipelineHandler.handle_remaining_calls()`.
  4. `plan_next_pipeline_step()` determines:
     - How to feed the previous output path into the next tool's input path (`chain_output_to_input()`).
     - Whether intermediate metadata filtering is available.
  5. If age/gender metadata is present, prompts user with a filter criteria dialog (`_show_filter_criteria_dialog()`).
  6. Filters the items using `apply_metadata_filter()` and updates `pipeline_metadata_filter_criteria` in `jobs.db`.
  7. Calls `load_and_show_form()` with chained arguments, preparing the next step form for user review and execution.
- **Code Handlers:**
  - `frontend/pages/chatbot/handlers/pipeline.py`: `PipelineHandler.handle_remaining_calls()`, `_show_filter_criteria_dialog()`
  - `frontend/pages/chatbot/handlers/pipeline_planner.py`: `plan_next_pipeline_step()`, `inject_filtered_paths_into_request()`
  - `frontend/chatbot/multi_tool_handler.py`: `chain_output_to_input()`, `apply_metadata_filter()`
  - `frontend/chatbot/pipeline_context.py`: `inject_pipeline_path()`, `get_pipeline_output_path()`
  - `frontend/database/job_db_pipeline.py`: Pipeline lineage and metadata criteria persistence

---

## 8. Chat History & Tool Re-run

### Scenario 8.1: Viewing Past Conversations
- **User Action:** User opens History from the chat drawer or clicks "Load Conversation".
- **Runtime Journey:**
  1. `show_history_dialog()` queries `ChatHistoryDB.get_all_conversations()` filtered by active case.
  2. User selects a past conversation.
  3. `load_conversation()` clears current view and replays conversation messages using `render_message()`.
- **Code Handlers:**
  - `frontend/components/chat/dialogs.py`: `show_history_dialog()`
  - `frontend/components/chat/view.py`: `load_conversation()`, `view_conversation()`
  - `frontend/database/chat_history_db.py`: `ChatHistoryDB.get_all_conversations()`, `get_messages()`

### Scenario 8.2: Re-running a Historical Tool Call
- **User Action:** User clicks "Re-run Job" on an earlier tool message, or visits `/chatbot?rerun=<message_id>`.
- **Runtime Journey:**
  1. Entry point triggers `handle_rerun_parameter(message_id)` or `rerun_tool_call(message_id)`.
  2. Resolves tool message via `ChatbotPage.handle_rerun_tool()`.
  3. `_resolve_rerun_arguments()` extracts persisted parameters, falling back to request snapshots in `jobs.db` if the history record omitted them.
  4. Triggers `_re_run_tool(endpoint, arguments)` which re-displays the form pre-filled with historical parameters.
- **Code Handlers:**
  - `frontend/components/chat/view.py`: `rerun_tool_call()`
  - `frontend/pages/chatbot/routes.py`: `handle_rerun_parameter()`, `chatbot_page(rerun=...)`
  - `frontend/pages/chatbot/history_ui.py`: `_append_rerun_job_button()`
  - `frontend/pages/chatbot/chat_page.py`: `handle_rerun_tool()`, `_resolve_rerun_arguments()`, `_re_run_tool()`

---

## 9. Job Monitoring & Inspection (`/jobs`)

### Scenario 9.1: Inspecting Job Status & Logs
- **User Action:** User navigates to `/jobs` or clicks a specific job `/jobs/{job_id}`.
- **Runtime Journey:**
  1. `JobsPage.render()` fetches jobs from `JobDB` scoped to the current user and active case.
  2. Table displays status chips (`Pending`, `In Progress`, `Completed`, `Failed`), duration, and endpoints.
  3. Clicking a job navigates to `detail.py`, which renders full request parameters, response JSON, and execution logs.
- **Code Handlers:**
  - `frontend/pages/jobs/list.py`: `JobsPage.render()`
  - `frontend/pages/jobs/job_list.py`: Table component with search and status filters
  - `frontend/pages/jobs/detail.py`: Individual job inspector
  - `frontend/database/job_db_queries.py`: `fetch_all_jobs_for_current_user()`, `fetch_job_by_uid()`

---

## 10. System Logs & Diagnostics (`/logs`)

### Scenario 10.1: Real-Time Diagnostic Log Viewer
- **User Action:** User navigates to `/logs`.
- **Runtime Journey:**
  1. `LogsPage` reads recent log records captured by `frontend/utils/logging.py`.
  2. Displays searchable, filterable logs by level (`INFO`, `WARNING`, `ERROR`).
  3. Provides a "Clear" and "Export" action for troubleshooting.
- **Code Handlers:**
  - `frontend/pages/logs.py`: `LogsPage`
  - `frontend/components/logs.py`: Log table widget
  - `frontend/utils/logging.py`: In-memory log buffer and log formatting

---

## 11. Model & Plugin Catalog (`/models`)

### Scenario 11.1: Plugin Capability & Model Status Inspection
- **User Action:** User navigates to `/models`.
- **Runtime Journey:**
  1. `ModelsPage.render()` reads cached model records from `model_cache.py`.
  2. Displays cards for each model/plugin with supported endpoints, task descriptions, and device requirements (CPU/GPU).
  3. User can click "Refresh" to trigger a fresh sync from `/api/models`.
- **Code Handlers:**
  - `frontend/pages/models.py`: `ModelsPage`
  - `frontend/components/models.py`: `render_model_card()`
  - `frontend/database/model_cache.py`: `get_all_models()`, `cache_models()`
  - `frontend/api_client.py`: `ApiClient.get("/models")`
