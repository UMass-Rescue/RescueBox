# Chatbot Module Tests

This document describes the test suite for the refactored chatbot module.

## Test Structure

### Unit Tests (`tests/unit/`)

#### `test_chatbot_utils.py`
Tests for utility functions:
- **`normalize_arguments`**: Tests argument key normalization (e.g., `input_directory` → `input_dir`)
- **`is_rescuebox_request`**: Tests input filtering for valid/invalid forensic requests
- **`get_rejection_message`**: Tests rejection message generation

**Key Test Cases:**
- Normalization of common key variations
- Endpoint-specific normalization (age_gender, deepfake, etc.)
- Filtering of blocked patterns (weather, jokes, recipes)
- Path detection for valid requests
- Case-insensitive normalization

#### `test_chatbot_config.py`
Tests for configuration and tool registry:
- **`ChatbotConfig`**: Tests default and custom configuration values
- **`ToolRegistry`**: Tests tool registry structure and consistency

**Key Test Cases:**
- Default configuration values
- Custom configuration
- Slash commands mapping
- Tool menu structure
- Fallback endpoints
- Blocked patterns
- RescueBox keywords
- Help text generation

#### `test_chatbot_core.py`
Tests for core business logic:
- **`ChatbotCore`**: Tests API interactions, form creation, job submission

**Key Test Cases:**
- Task schema fetching from endpoints
- Argument conversion to initial values
- Argument normalization during conversion
- Job submission
- Granite model tool call parsing (both Ollama API and direct GGUF loading)
- Direct GGUF model loading via llama-cpp-python (call_granite_model_direct)
- Model caching and lazy loading
- Error handling (import errors, file not found, inference errors)

#### `test_chatbot_message_handler.py`
Tests for message routing and handling:
- **`MessageHandler`**: Tests message routing, slash commands, smart analyze

**Key Test Cases:**
- Input method detection (slash command vs smart analyze)
- Slash command handling (`/help`, `/models`, `/analyze`, etc.)
- Smart analyze flow with Granite model
- Input filtering integration
- Argument normalization in message flow
- Error handling

### Integration Tests (`tests/integration/`)

#### `test_chatbot_flow.py`
End-to-end integration tests:
- **Complete flows**: Slash command → form, Smart analyze → form
- **Argument normalization**: Tests normalization in real flow
- **Input filtering**: Tests filtering in message handler
- **Job submission**: Tests full job submission flow
- **Help and tool picker**: Tests special commands

#### `test_pages.py` (Updated)
UI integration tests using NiceGUI User fixture:
- **Page loading**: Tests chatbot page renders correctly
- **Help command**: Tests `/help` command flow
- **Model picker**: Tests `/models` command flow
- **Slash commands**: Tests slash command execution

## Running Tests

### Run all chatbot tests:
```bash
pytest frontend/tests/unit/test_chatbot_*.py -v
pytest frontend/tests/integration/test_chatbot_flow.py -v
```

### Run specific test file:
```bash
pytest frontend/tests/unit/test_chatbot_utils.py -v
```

### Run with coverage:
```bash
pytest frontend/tests/ --cov=frontend.chatbot --cov-report=html
```

## Test Coverage

The test suite covers:

1. **Utility Functions** (100% coverage target)
   - Argument normalization
   - Input filtering
   - Rejection messages

2. **Configuration** (100% coverage target)
   - Config defaults and customization
   - Tool registry structure
   - Help text generation

3. **Core Logic** (90%+ coverage target)
   - Schema fetching
   - Form creation
   - Job submission
   - Granite model integration (Ollama API and direct GGUF loading)
   - Direct model loading with llama-cpp-python
   - Model caching and resource cleanup

4. **Message Handling** (90%+ coverage target)
   - Message routing
   - Slash commands
   - Smart analyze
   - Filtering integration

5. **Integration Flows** (Key paths covered)
   - Complete user flows
   - Error scenarios
   - Edge cases

## Key Features Tested

### Argument Normalization
- Maps common variations (`input_directory` → `input_dir`)
- Endpoint-specific overrides (age_gender → `image_directory`)
- Case-insensitive handling

### Input Filtering
- Blocks non-forensic requests (weather, jokes, recipes)
- Allows valid forensic keywords
- Path detection for file operations
- Configurable enable/disable

### Message Routing
- Detects slash commands vs natural language
- Routes to appropriate handlers
- Integrates filtering and normalization

### Error Handling
- Graceful degradation when Granite model unavailable
- Clear error messages
- Validation failures
- Import errors for llama-cpp-python
- File not found errors for GGUF model files
- Inference errors during model execution

## Mocking Strategy

- **HTTP Clients**: Mocked `httpx.AsyncClient` for API calls
- **Ollama Client**: Mocked for Granite model calls
- **llama-cpp-python**: Mocked `Llama` class and model responses for unit tests
- **UI Components**: NiceGUI `User` fixture for UI testing
- **File System**: Temporary directories for file operations
- **Model Loading**: Mocked model loading and inference for unit tests

## Future Enhancements

1. Add performance tests for normalization functions
2. Add stress tests for concurrent message handling
3. Add UI interaction tests with real browser automation
4. Add tests for edge cases in argument normalization
5. Add tests for multi-tool call scenarios

## Tests for call_granite_model_direct

The `call_granite_model_direct` method has comprehensive unit test coverage:

### Unit Tests (test_chatbot_core.py)
- Import error handling (llama-cpp-python not installed)
- File not found handling
- Successful tool call parsing with `<tool_code>` tags
- JSON fallback parsing
- Multiple tool calls handling
- Empty response handling
- No tool call detection
- Inference error handling
- Model caching (lazy loading verification)

### Integration Tests
- Real model loading and inference (test_ollama_granite_integration.py)
- Multi-tool call scenarios (test_multi_tool_calls_integration.py)
- Chatbot flow integration (test_chatbot_flow_integration.py)

**Note**: All tests correctly verify that `call_granite_model_direct` returns `Optional[list[Dict[str, Any]]]` (a list of tool calls), not a single dict.

