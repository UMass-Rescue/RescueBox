# TODO: Update Tests for Input Enable/Disable Feature

**Rule implemented**: Input is enabled only when there is no pending chat interaction and the system is ready for a new prompt.

**Feature scope**: `set_input_enabled()`, `set_input_area()`, `on_form_cancel`, `load_and_show_form(on_form_cancel=...)`, and related flows.

---

## 1. Unit Tests to Update

### 1.1 `test_chatbot_forms_errors.py`
- [ ] **load_and_show_form calls** – All tests pass `Mock()` for `on_form_submit`; `on_form_cancel` is optional (default `None`). Verify existing tests still pass.
- [ ] **Add**: Test that `load_and_show_form` accepts `on_form_cancel` and passes it to `core.create_input_form`.
- [ ] **Add**: Test that when form creation fails (no schema, etc.), `on_form_cancel` is never called.

### 1.2 `chatbot_test_utils.py` / Fixtures
- [ ] **mock_chatbot** – Ensure `state_manager` mock has `set_input_enabled` and `set_input_area` if tests assert on them.
- [ ] **create_mock_chatbot_page** – Add `state_manager.set_input_enabled` and `state_manager.set_input_area` as MagicMocks if needed.

### 1.3 `test_form_components.py` / `test_form_generator.py`
- [ ] **FormGenerator.generate_form** – Tests call `generate_form(..., onSubmit=...)` without `onCancel`. Verify optional `onCancel` works (default `None`).
- [ ] **Add**: Test that `onCancel` is called when user clicks Cancel (integration test).

### 1.4 `test_ui_integration.py`
- [ ] **create_chat_ui** – Now returns 4 values `(chat_container, input_field, status_label, input_area)`. Update any test that unpacks the return value.
- [ ] **state_manager** – Test `ChatbotStateManager` has `set_input_enabled`, `set_input_area`, and that they can be called without error when `input_area` is `None`.

### 1.5 `test_conversation_loading.py`
- [ ] **mock_chatbot** – `state_manager` may need `set_input_enabled` and `set_input_area` for any assertions on new-conversation flow.
- [ ] **Add**: Test that new conversation flow calls `set_input_enabled(True)` (if testable via mock).

### 1.6 `test_job_background_submission.py`
- [ ] **form_handler.state_manager** – Ensure mock has `set_input_enabled` for job completion/failure paths.
- [ ] **Add**: Test that job success (no remaining calls) triggers `set_input_enabled(True)`.
- [ ] **Add**: Test that job failure triggers `set_input_enabled(True)`.

---

## 2. Unit Tests to Add

### 2.1 State Manager
- [ ] **test_state_manager.py** (new or in existing test file):
  - `test_set_input_enabled_with_input_area` – `set_input_enabled(False)` calls `disable()` on field and button.
  - `test_set_input_enabled_with_input_area_enable` – `set_input_enabled(True)` calls `enable()` on field and button.
  - `test_set_input_enabled_no_input_area` – No error when `input_area` and `input_field` are `None`.
  - `test_set_input_area_sets_input_field` – `set_input_area` populates `input_field` when missing.

### 2.2 Message Processor
- [ ] **test_message_processor.py** (or extend existing):
  - Test that `send_message` disables input at start.
  - Test that `message` result type enables input.
  - Test that `tool_picker` result type keeps input disabled.
  - Test that `analysis_picker`, `show_form`, `multi_tool_calls` keep input disabled.

### 2.3 Result Processor
- [ ] Test that `set_input_enabled_callback` is invoked with correct boolean for each result type.

### 2.4 Callback Manager
- [ ] Test that `get_result_processor_callbacks` includes `set_input_enabled_callback` when `state_manager` exists.

### 2.5 Job Submission Orchestrator
- [ ] Test that job success (no `remaining_calls`) calls `set_input_enabled(True)`.
- [ ] Test that job failure in `_do_submit` calls `set_input_enabled(True)`.
- [ ] Test that `handle_remaining_calls` passes `on_form_cancel` to `load_and_show_form`.

---

## 3. Integration Tests to Update/Add

### 3.1 `test_form_generator.py`
- [ ] **generate_form** – Add `onCancel` param to call if testing cancel flow.
- [ ] **Add**: Test that Cancel button triggers `onCancel` callback when provided.

### 3.2 `test_pages_integration.py` / `test_pages.py`
- [ ] **test_chatbot_page_loads** – Verify page still renders (input enabled by default).
- [ ] **test_chatbot_tool_picker_command** – After tool picker, input should be disabled (if testable).
- [ ] **Add**: Smoke test for new conversation → input enabled.

### 3.3 `test_ui_integration.py`
- [ ] **test_chatbot_page_rendering** – Ensure 4-tuple return from `create_chat_ui` is handled.
- [ ] **test_message_to_form_to_result_workflow** – May need mock updates for `set_input_enabled`.

---

## 4. Fixtures and Conftest

### 4.1 `conftest.py` (unit and integration)
- [ ] **mock_chatbot** – Add `state_manager.set_input_enabled = MagicMock()`, `state_manager.set_input_area = MagicMock()` if tests fail on missing attributes.
- [ ] **mock_state_manager** – If a shared fixture exists, ensure it has `set_input_enabled` and `set_input_area`.

---

## 5. Execution Order

1. Run existing tests to find regressions:
   ```bash
   poetry run pytest frontend/tests/unit/test_chatbot_forms_errors.py -v
   poetry run pytest frontend/tests/unit/test_form_components.py -v
   poetry run pytest frontend/tests/integration/test_form_generator.py -v
   poetry run pytest frontend/tests/integration/test_ui_integration.py -v
   poetry run pytest frontend/tests/unit/test_conversation_loading.py -v
   ```
2. Fix failing tests (mainly return value unpacking and mock attributes).
3. Add new unit tests for `state_manager`, `message_processor`, `result_processor`, `callback_manager`, `job_submission_orchestrator`.
4. Add integration tests for cancel flow and input enable/disable behavior where feasible.

---

## 6. Notes

- `on_form_cancel` is optional everywhere; existing callers that omit it should continue to work.
- `create_chat_ui` return value changed from 3 to 4 elements; update any unpacking.
- Mocks may need `set_input_enabled` and `set_input_area` only if tests assert or trigger code that calls them.
