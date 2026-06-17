# Integration Test Mock Analysis

This document analyzes which integration tests use mocks vs. real dependencies.

**Last Updated**: After refactoring to use real dependencies where possible.

## Tests with REAL Dependencies (No Mocks) ✅

### 1. `test_api_endpoints.py`
- **Status**: ✅ **NO MOCKS** - Real HTTP calls to backend API
- **Dependencies**: Backend API running at `http://localhost:8000`
- **What it tests**: Actual backend API endpoints (`/models`, `/servers`, etc.)
- **Mocks used**: None

### 2. `test_ollama_granite_integration.py`
- **Status**: ✅ **NO MOCKS** - Real HTTP calls to Ollama API
- **Dependencies**: Ollama server running at `http://localhost:11434`, Granite model available
- **What it tests**: Actual Ollama API calls, Granite model tool calling
- **Mocks used**: None

### 3. `test_stepper_ui.py`
- **Status**: ✅ **NO MOCKS** - Real NiceGUI UI testing
- **Dependencies**: NiceGUI User fixture (no external services)
- **What it tests**: UI component rendering
- **Mocks used**: None

### 4. `test_form_generator.py`
- **Status**: ✅ **NO MOCKS** (imports `patch` but doesn't use it)
- **Dependencies**: NiceGUI User fixture (no external services)
- **What it tests**: Form generator UI component
- **Mocks used**: None (patch imported but unused)

## Tests WITH Real Dependencies (After Refactoring) ✅

### 1. `test_chatbot_flow_integration.py` (NEW)
- **Status**: ✅ **NO MOCKS** - Real API and Ollama clients
- **Dependencies**: Backend API + Ollama server
- **What it tests**: Complete chatbot flow with real API and Ollama calls
- **Mocks used**: None

### 2. `test_pages_integration.py` (NEW)
- **Status**: ✅ **NO MOCKS** - Real API client
- **Dependencies**: Backend API
- **What it tests**: Page rendering with real API responses
- **Mocks used**: None

### 3. `test_chatbot_storage_integration.py` (UPDATED)
- **Status**: ✅ **NO MOCKS** - Removed handler mock
- **Dependencies**: NiceGUI storage (real), database (real)
- **What it tests**: Storage integration with NiceGUI
- **Mocks used**: None (removed handler processing mock)

## Tests WITH Mocks (Kept for Fast Unit-Style Testing) ⚠️

### 1. `test_chatbot_flow.py` (LEGACY - Uses Mocks)
- **Status**: ⚠️ **USES MOCKS** - Mocks API client and Ollama client
- **Dependencies**: None (all mocked)
- **What it tests**: Chatbot flow logic with mocked responses
- **Mocks used**:
  - `AsyncMock` for `api_client` (API calls)
  - `AsyncMock` for `ollama_client` (Ollama calls)
  - Mock responses for schema, job submission, tool calls
- **Note**: File header updated to indicate mocks are used. Kept for fast unit-style testing.

### 2. `test_pages.py` (LEGACY - Uses Mocks)
- **Status**: ⚠️ **USES MOCKS** - Uses `mock_api_client` fixture
- **Dependencies**: NiceGUI User fixture (UI is real, API is mocked)
- **What it tests**: Page UI rendering with mocked API responses
- **Mocks used**:
  - `mock_api_client` fixture mocks all API calls
  - Mock responses for `/models`, `/servers`, `/jobs`, etc.
- **Note**: File header updated to indicate mocks are used. Kept for fast unit-style testing.

### 3. `test_notifications_ui.py`
- **Status**: ⚠️ **USES MOCKS** - Mocks `nicegui.ui.notify`
- **Dependencies**: NiceGUI User fixture (UI is real, notify is mocked)
- **What it tests**: Notification function calls (not actual notification display)
- **Mocks used**:
  - `patch('nicegui.ui.notify')` - Mocks notification display
- **Note**: Acceptable for UI testing (notifications are side effects). File header documents why mock is used.

## Summary

| Test File | Real Dependencies | Mocks Used | Category | Status |
|-----------|------------------|------------|----------|--------|
| `test_api_endpoints.py` | ✅ Backend API | None | True Integration | ✅ Current |
| `test_ollama_granite_integration.py` | ✅ Ollama API | None | True Integration | ✅ Current |
| `test_stepper_ui.py` | ✅ NiceGUI UI | None | UI Integration | ✅ Current |
| `test_form_generator.py` | ✅ NiceGUI UI | None | UI Integration | ✅ Current |
| `test_chatbot_flow_integration.py` | ✅ Backend API + Ollama | None | True Integration | ✅ **NEW** |
| `test_pages_integration.py` | ✅ Backend API | None | True Integration | ✅ **NEW** |
| `test_chatbot_storage_integration.py` | ✅ Storage/DB | None | True Integration | ✅ **UPDATED** |
| `test_chatbot_flow.py` | ❌ None | ✅ All API/Ollama | Unit-style (fast) | ⚠️ **LEGACY** |
| `test_pages.py` | ⚠️ NiceGUI UI | ✅ API calls | Unit-style (fast) | ⚠️ **LEGACY** |
| `test_notifications_ui.py` | ✅ NiceGUI UI | ⚠️ Notification display | UI Integration | ✅ Acceptable |

## Refactoring Status

✅ **COMPLETED**:
1. Created `test_chatbot_flow_integration.py` with real API and Ollama clients
2. Created `test_pages_integration.py` with real API client
3. Removed mock from `test_chatbot_storage_integration.py`
4. Documented mock usage in legacy test files
5. Updated `mock_api_client` fixture with deprecation note

## Recommendations

1. ✅ **Use integration versions for CI/CD** - Run `test_*_integration.py` files for true integration testing
2. ✅ **Keep legacy files for fast local testing** - `test_chatbot_flow.py` and `test_pages.py` can be used for quick iteration
3. ✅ **Document mock usage** - All test files now have clear headers indicating mock usage
4. ✅ **Notifications mock is acceptable** - UI side effects are hard to test directly, mock is reasonable

## True Integration Tests (All Real Dependencies)

To run tests that use ONLY real dependencies:

```bash
# Backend API integration tests
pytest frontend/tests/integration/test_api_endpoints.py -v -m api

# Ollama integration tests
pytest frontend/tests/integration/test_ollama_granite_integration.py -v -m ollama

# Chatbot flow with real API and Ollama
pytest frontend/tests/integration/test_chatbot_flow_integration.py -v -m "api and ollama"

# Pages with real API
pytest frontend/tests/integration/test_pages_integration.py -v -m api

# UI integration tests (no external dependencies)
pytest frontend/tests/integration/test_stepper_ui.py -v
pytest frontend/tests/integration/test_form_generator.py -v

# Storage integration (no mocks)
pytest frontend/tests/integration/test_chatbot_storage_integration.py -v
```

