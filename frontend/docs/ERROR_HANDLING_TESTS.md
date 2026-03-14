# Error Handling Test Coverage

## Overview

This document describes the comprehensive test suite created to cover all error handling improvements made to the RescueBox frontend codebase.

## Test Files Created

### 1. `test_chatbot_core_errors.py`

Tests for ChatbotCore error handling:

- **HTTP Error Handling**:
  - `test_get_task_schema_http_404_error`: Tests 404 error handling when fetching task schema
  - `test_get_task_schema_http_500_error`: Tests 500 error handling when fetching task schema
  - `test_submit_job_http_404_error`: Tests 404 error handling when submitting job
  - `test_submit_job_http_500_error`: Tests 500 error handling when submitting job

- **Network Error Handling**:
  - `test_get_task_schema_network_error`: Tests network error (RequestError) handling
  - `test_submit_job_network_error`: Tests network error handling when submitting job
  - `test_call_granite_model_network_error`: Tests network error handling when calling Granite model

- **JSON Parsing Errors**:
  - `test_get_task_schema_invalid_json`: Tests invalid JSON response handling
  - `test_submit_job_invalid_json_response`: Tests invalid JSON response handling when submitting job
  - `test_call_granite_model_invalid_response_format`: Tests invalid response format from Granite model

- **Format Validation Errors**:
  - `test_get_task_schema_invalid_schema_format`: Tests invalid schema format (missing required fields)
  - `test_submit_job_invalid_response_format`: Tests invalid response format when submitting job
  - `test_call_granite_model_missing_response_key`: Tests missing 'response' key in Granite model response

### 2. `test_results_utils_errors.py`

Tests for results utils error handling (file/folder operations):

- **Path Validation**:
  - `test_open_file_empty_path`: Tests handling of empty file path
  - `test_open_folder_empty_path`: Tests handling of empty folder path

- **File/Folder Existence**:
  - `test_open_file_nonexistent_file`: Tests handling of nonexistent file
  - `test_open_file_path_is_directory`: Tests handling of path that is a directory, not a file
  - `test_open_folder_nonexistent_folder`: Tests handling of nonexistent folder
  - `test_open_folder_path_is_file`: Tests handling of path that is a file, not a directory

- **Platform-Specific Errors**:
  - `test_open_file_file_not_found_error_windows`: Tests FileNotFoundError on Windows
  - `test_open_file_permission_error_windows`: Tests PermissionError on Windows
  - `test_open_file_subprocess_error_macos`: Tests subprocess error on macOS
  - `test_open_folder_file_not_found_error`: Tests FileNotFoundError when opening folder
  - `test_open_folder_permission_error`: Tests PermissionError when opening folder
  - `test_open_folder_subprocess_error`: Tests subprocess error when opening folder

- **Generic Exception Handling**:
  - `test_open_file_generic_exception`: Tests handling of generic exception

### 3. `test_form_handlers_errors.py`

Tests for form handlers error handling:

- **Validation Errors**:
  - `test_handle_form_submit_validation_error`: Tests handling of validation error during form submission

- **Data Collection Errors**:
  - `test_handle_form_submit_data_collection_error`: Tests handling of error during form data collection
  - `test_collect_form_data_missing_widget`: Tests collecting form data when widget is missing
  - `test_collect_form_data_widget_value_error`: Tests collecting form data when widget value access fails

- **Submission Errors**:
  - `test_handle_form_submit_submit_callback_error`: Tests handling of error in submit callback
  - `test_handle_form_submit_no_callback`: Tests handling of missing submit callback

- **Unexpected Errors**:
  - `test_handle_form_submit_unexpected_error`: Tests handling of unexpected error during form submission

### 4. `test_file_renderers_errors.py`

Tests for file renderers error handling:

- **Path Validation**:
  - `test_render_file_empty_path`: Tests handling of file response with empty path

- **File Existence**:
  - `test_render_file_nonexistent_image`: Tests handling of nonexistent image file

- **Rendering Errors**:
  - `test_render_file_image_load_error`: Tests handling of error loading image
  - `test_render_file_generic_exception`: Tests handling of generic exception during file rendering

### 5. `test_database_errors.py`

Tests for database error handling:

- **SQLite Errors**:
  - `test_create_conversation_integrity_error`: Tests handling of IntegrityError when creating conversation
  - `test_create_conversation_sqlite_error`: Tests handling of generic sqlite3.Error when creating conversation

- **Unexpected Errors**:
  - `test_create_conversation_unexpected_error`: Tests handling of unexpected error when creating conversation

- **Query Errors**:
  - `test_get_conversation_not_found`: Tests handling of conversation not found (returns None, doesn't raise)
  - `test_get_all_conversations_with_error`: Tests handling of error when getting all conversations

### 6. `test_chatbot_forms_errors.py`

Tests for chatbot forms error handling:

- **Schema Fetching Errors**:
  - `test_load_and_show_form_no_schema`: Tests handling of no schema returned
  - `test_load_and_show_form_schema_fetch_error`: Tests handling of error fetching schema

- **Form Creation Errors**:
  - `test_load_and_show_form_initial_values_error`: Tests handling of error converting arguments to initial values
  - `test_load_and_show_form_create_form_error`: Tests handling of error creating form

- **Results Rendering Errors**:
  - `test_show_results_invalid_response_body`: Tests handling of invalid response body
  - `test_show_results_rendering_error`: Tests handling of error during results rendering

## Updated Tests

### `test_chatbot_core.py`

Updated existing test to use correct exception types:
- `test_get_task_schema_from_endpoint_error`: Updated to use `httpx.HTTPStatusError` instead of generic `Exception`

## Test Coverage Summary

### Error Types Covered

1. **HTTP Errors**:
   - 404 (Not Found)
   - 500 (Internal Server Error)
   - HTTPStatusError exceptions

2. **Network Errors**:
   - RequestError (connection refused, timeout, etc.)
   - Connection errors

3. **Data Format Errors**:
   - Invalid JSON
   - Missing required fields
   - Invalid response format

4. **File System Errors**:
   - FileNotFoundError
   - PermissionError
   - Path validation errors

5. **Database Errors**:
   - IntegrityError (constraint violations)
   - sqlite3.Error (generic database errors)

6. **Validation Errors**:
   - Form validation failures
   - Missing widgets/fields
   - Invalid data formats

7. **Rendering Errors**:
   - Image loading failures
   - UI component errors

## Running the Tests

### Run All Error Handling Tests

```bash
pytest frontend/tests/unit/test_chatbot_core_errors.py frontend/tests/unit/test_results_utils_errors.py frontend/tests/unit/test_form_handlers_errors.py frontend/tests/unit/test_file_renderers_errors.py frontend/tests/unit/test_database_errors.py frontend/tests/unit/test_chatbot_forms_errors.py -v
```

### Run Individual Test Files

```bash
# Chatbot core errors
pytest frontend/tests/unit/test_chatbot_core_errors.py -v

# Results utils errors
pytest frontend/tests/unit/test_results_utils_errors.py -v

# Form handlers errors
pytest frontend/tests/unit/test_form_handlers_errors.py -v

# File renderers errors
pytest frontend/tests/unit/test_file_renderers_errors.py -v

# Database errors
pytest frontend/tests/unit/test_database_errors.py -v

# Chatbot forms errors
pytest frontend/tests/unit/test_chatbot_forms_errors.py -v
```

## Test Patterns Used

### Mocking HTTP Clients

```python
mock_response = AsyncMock()
mock_response.status_code = 404
mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(...)
core.api_client.get = AsyncMock(return_value=mock_response)
```

### Mocking File System

```python
with patch('frontend.components.results.results_utils.os.path.exists', return_value=False):
    open_file("/nonexistent/file.txt")
```

### Mocking UI Components

```python
with patch('frontend.components.results.results_utils.ui') as mock_ui:
    open_file("/tmp/test.txt")
    mock_ui.notify.assert_called_once()
```

### Testing Exception Handling

```python
with pytest.raises(Exception, match="Expected error message"):
    await function_that_should_raise()
```

## Coverage Goals

All error handling improvements are now covered by tests:

- ✅ HTTP error handling (404, 500, network errors)
- ✅ JSON parsing errors
- ✅ File system errors (FileNotFoundError, PermissionError)
- ✅ Database errors (IntegrityError, sqlite3.Error)
- ✅ Validation errors
- ✅ Rendering errors
- ✅ Form submission errors
- ✅ API call errors

## Future Enhancements

Potential areas for additional test coverage:

1. Integration tests for error scenarios with real API calls
2. UI integration tests for error message display
3. End-to-end error flow tests
4. Performance tests for error handling overhead
5. Stress tests with multiple concurrent errors

## Related Documentation

- See `ERROR_HANDLING_REVIEW.md` for details on error handling improvements
- See `COMPLEXITY_COMPARISON.md` for architecture overview
- See `readme.md` for general frontend documentation

