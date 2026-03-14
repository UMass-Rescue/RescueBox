# Integration Tests for Frontend

This directory contains integration tests that verify the frontend works correctly with the backend API.

## Test Files

### `test_api_endpoints.py`
Integration tests for backend API endpoints. These tests make actual HTTP requests to the running backend.

**Requires:** Backend API running at `http://localhost:8000`

**Tests:**
- `GET /models` - List all models
- `GET /models/{model_uid}` - Get model details
- `GET /models/{model_uid}/info` - Get model info (alias)
- `GET /servers` - List all servers
- `GET /servers/{model_uid}/status` - Get server status
- Error handling (404 responses)
- Endpoint consistency

### `test_pages.py`
Integration tests for NiceGUI pages using the User fixture.

**Tests:**
- Index page loading and navigation
- Models page loading and display
- Chatbot page functionality
- Jobs page loading and display

### `test_chatbot_flow.py`
Integration tests for chatbot message flow and tool selection.

### `test_form_generator.py`
Integration tests for form generation component.

## Running Tests

### Prerequisites

1. **Backend API must be running**:
   ```bash
   python -m rb.api.main
   ```

2. **Install test dependencies**:
   ```bash
   pip install pytest pytest-asyncio httpx nicegui
   ```

### Run All Integration Tests

```bash
# Run all integration tests
pytest frontend/tests/integration/ -v

# Run with API marker (requires backend)
pytest frontend/tests/integration/ -m api -v

# Run without API tests (no backend required)
pytest frontend/tests/integration/ -m "not api" -v
```

### Run Specific Test Files

```bash
# Test API endpoints (requires backend)
pytest frontend/tests/integration/test_api_endpoints.py -v

# Test pages (uses mocks, no backend required)
pytest frontend/tests/integration/test_pages.py -v

# Test chatbot flow
pytest frontend/tests/integration/test_chatbot_flow.py -v
```

### Run Specific Test Classes

```bash
# Test models endpoints
pytest frontend/tests/integration/test_api_endpoints.py::TestModelsEndpoints -v

# Test servers endpoints
pytest frontend/tests/integration/test_api_endpoints.py::TestServersEndpoints -v
```

### Run Specific Tests

```bash
# Test getting models list
pytest frontend/tests/integration/test_api_endpoints.py::TestModelsEndpoints::test_get_models_list -v
```

## Test Markers

Tests are marked with pytest markers:

- `@pytest.mark.api` - Requires backend API to be running
- `@pytest.mark.integration` - Integration test (not unit test)
- `@pytest.mark.asyncio` - Async test function

## Environment Variables

- `API_BASE_URL` - Override backend API base URL (default: `http://localhost:8000`)

Example:
```bash
API_BASE_URL=http://localhost:9000
pytest frontend/tests/integration/test_api_endpoints.py -v
```

## Troubleshooting

### Tests Skip with "Backend API not available"

**Solution:** Start the backend API:
```bash
python -m rb.api.main
```

## Test Validation

### Tests Fail with Connection Errors

**Check:**
1. Backend is running on the expected port (default: 8000)
2. No firewall blocking connections
3. Backend is accessible from test environment

### Tests Fail with 404 Errors

**Check:**
1. Backend has plugins registered
2. Model UIDs in tests match actual plugin names
3. Backend routes are properly registered

## Test Coverage

The integration tests verify:
- ✅ All backend API endpoints return correct status codes
- ✅ Response structures match expected format
- ✅ Error handling (404 for invalid requests)
- ✅ Endpoint consistency (models ↔ servers)
- ✅ Complete user flows (list → details → status)

