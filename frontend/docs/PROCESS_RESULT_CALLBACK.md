# Process Result Callback - Complete Flow Explanation

## Overview

The `process_result_callback` is a critical callback function that handles result processing after a user message has been sent and processed by the chatbot. It serves as the coordination point between message sending and result handling in the refactored chatbot architecture.

## Architecture Context

The callback pattern is part of the refactored chatbot system that separates concerns:

- **MessageProcessor**: Handles message sending and initial processing
- **ChatbotPage**: Orchestrates the overall flow and provides callbacks
- **ResultProcessor**: Executes the actual result handling logic
- **FormSubmitHandler**: Manages form submissions and job execution

## Flow Diagram
Key Flow Points:

MessageProcessor sends the message and gets a result

process_result_callback (→ ChatbotPage._process_result) coordinates what to do with that result

ResultProcessor executes the actual result handling logic based on result type

The callback enables the MessageProcessor to focus solely on sending messages, while delegating result interpretation to the higher-level ChatbotPage orchestrator.

Depending on the result['type'], different actions are taken:
    'show_form' → Loads a form for user input (e.g., tool parameters)
    'multi_tool_calls' → Starts sequential execution of multiple tools
    'message' → Adds a simple text response to chat
    'error' → Shows an error message
    'tool_picker' → Shows tool selection UI
    'analysis_picker' → Shows analysis type selection UI

```
User Message → MessageProcessor.send_message()
                                      ↓
                         process_result_callback invoked
                                      ↓
                ChatbotPage._process_result() called
                                      ↓
          ResultProcessor.process_result() executed
                                      ↓
              Final UI actions (forms, messages, etc.)
```

## Detailed Flow

### 1. Message Sending (`MessageProcessor.send_message()`)

```python
async def send_message(self, message_text: str, process_result_callback: Callable, ...):
    # Process message through chatbot core
    result = await self.message_handler.handle_message(message_text)

    # INVOKE THE CALLBACK - This is where process_result_callback is called
    await process_result_callback(
        result=result,                          # The chatbot response
        add_message_callback=add_message_callback,
        show_error_callback=show_error_callback,
        update_status_callback=update_status_callback
    )
```

### 2. Callback Implementation (`ChatbotPage._process_result()`)

```python
async def _process_result(self, result: dict):
    """Process handler result using the result processor."""

    # Special handling for analysis picker
    if result.get('type') == 'analysis_picker':
        # Show analysis picker UI and handle selection
        await self.result_processor.process_result(...)

    else:
        # Normal result processing for all other types
        await self.result_processor.process_result(
            result=result,
            container=self.chat_container,
            core=self.core,
            add_message_callback=self._add_message,
            show_error_callback=self._show_error,
            update_status_callback=self._update_status
        )
```

### 3. Final Processing (`ResultProcessor.process_result()`)

```python
async def process_result(self, result: Dict[str, Any], ...):
    """Process a handler result and trigger appropriate actions."""

    result_type = result.get('type', 'unknown')

    # Route to appropriate handler based on result type
    if result_type == 'show_form':
        await self._handle_show_form(result, container, core, load_form_callback)

    elif result_type == 'multi_tool_calls':
        await self._handle_multi_tool_calls(result, container, load_form_callback, add_message_callback)

    elif result_type == 'message':
        await self._handle_message(result, add_message_callback)

    elif result_type == 'error':
        await self._handle_error(result, show_error_callback)

    elif result_type == 'tool_picker':
        await self._handle_tool_picker(result, container, add_message_callback)

    elif result_type == 'analysis_picker':
        await self._handle_analysis_picker(result, container, add_message_callback)
```

## Result Types Handled

### `show_form`
- **Purpose**: Load and display a form for user input (e.g., tool parameters)
- **Action**: Calls `load_and_show_form()` to render parameter input UI

### `multi_tool_calls`
- **Purpose**: Handle sequential execution of multiple tools
- **Action**: Starts with first tool call, chains subsequent calls via remaining_calls

### `message`
- **Purpose**: Add a simple text response to the chat
- **Action**: Calls `add_message_callback()` with the message content

### `error`
- **Purpose**: Display error messages to the user
- **Action**: Calls `show_error_callback()` with error details

### `tool_picker`
- **Purpose**: Show tool selection interface
- **Action**: Displays UI for selecting from available tools

### `analysis_picker`
- **Purpose**: Show analysis type selection interface
- **Action**: Displays UI for choosing analysis options

## Why This Design?

### 1. Separation of Concerns
- **MessageProcessor**: Focuses solely on sending messages and getting results
- **ChatbotPage**: Orchestrates the overall flow without knowing result details
- **ResultProcessor**: Handles the complexity of different result types

### 2. Callback Pattern Benefits
- **Flexibility**: Easy to change result handling without affecting message sending
- **Testability**: Each component can be tested independently
- **Extensibility**: New result types can be added without modifying existing code

### 3. Async Flow Support
- Supports complex async operations in result processing
- Allows for user interactions (form submissions, picker selections)
- Handles sequential operations (multi-tool calls)

## Callback Parameters

The `process_result_callback` receives these parameters:

- **`result`**: Dictionary containing the chatbot's response with `type` and other data
- **`add_message_callback`**: Function to add messages to the chat UI
- **`show_error_callback`**: Function to display errors to the user
- **`update_status_callback`**: Function to update the status bar

## Usage in Tests

The callback pattern also facilitates testing:

```python
# Mock callbacks for testing
async def mock_add_message(message):
    # Verify message was added correctly

async def mock_show_error(error):
    # Verify error handling

# Test the message processor
result = await message_processor.send_message(
    message_text="test",
    process_result_callback=mock_process_result,
    add_message_callback=mock_add_message,
    show_error_callback=mock_show_error,
    update_status_callback=mock_update_status
)
```

## Key Benefits

1. **Clean Architecture**: Clear separation between message sending and result processing
2. **Maintainable Code**: Changes to result handling don't affect message sending logic
3. **Testable Components**: Each part of the flow can be tested independently
4. **Extensible Design**: Easy to add new result types and processing logic
5. **Async Compatibility**: Full support for complex async operations and user interactions
