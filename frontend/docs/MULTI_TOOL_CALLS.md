# Multiple Tool Calls Support

## Overview

The chatbot now supports handling multiple tool calls from the Ollama Granite model in a single request. When the model returns multiple tool calls (e.g., "summarize images and detect fakes"), they are executed sequentially with automatic output chaining.

## Features

### 1. Multiple Tool Call Detection

The `call_granite_model` method now extracts **all** tool calls from the model response, not just the first one. It supports:
- Multiple `<tool_code>...</tool_code>` tags
- Multiple JSON objects in the response

### 2. Sequential Execution

Tool calls are executed one by one:
1. First tool call: Shows form with user inputs
2. User submits form → First call executes → Results displayed
3. Second tool call: Shows form with:
   - Output from first call chained as input directory (if applicable)
   - Original user parameters from before first call
   - Option for user to modify/adjust parameters
4. User submits form → Second call executes → Results displayed
5. Process continues for all tool calls

### 3. Output Chaining

The system automatically chains outputs between tool calls:
- **First call output** → Extracted output path/directory
- **Second call input** → Uses output path as input directory (if schema supports it)

**Example:**
- Call 1: `image_summary/summarize_images` → Output: `/output/summaries`
- Call 2: `deepfake_detection/give_prediction` → Input: `/output/summaries` (chained automatically)

### 4. Result History

All tool call results are:
- Displayed in the chat
- Saved to chat history
- Saved to job database
- Visible in chat history panel

Users can scroll up to see previous tool call results even after subsequent calls complete.

### 5. User Control

Users can:
- **Modify parameters** between calls (each call shows a form)
- **Review results** of previous calls before continuing
- **Stop the sequence** (just don't submit the next form)

## Implementation Details

### Modified Files

1. **`frontend/chatbot/core.py`**
   - `call_granite_model()`: Now returns `list[Dict]` instead of single `Dict`
   - Uses `re.findall()` to extract all tool calls from response

2. **`frontend/chatbot/message_handler.py`**
   - `handle_smart_analyze()`: Returns `'multi_tool_calls'` type for multiple calls
   - Validates all tool calls before returning

3. **`frontend/chatbot/multi_tool_handler.py` (NEW)**
   - `extract_output_path()`: Extracts output directory from ResponseBody
   - `chain_output_to_input()`: Chains output path to next call's input directory
   - `execute_tool_call_sequence()`: Orchestrates sequential execution

4. **`frontend/pages/chatbot/chatbot_handlers.py`**
   - `process_handler_result()`: Handles `'multi_tool_calls'` result type
   - `handle_form_submit()`: Continues with next tool call after current completes
   - Added `remaining_calls` parameter to pass through call sequence

5. **`frontend/pages/chatbot/chatbot.py`**
   - `load_and_show_form()`: Accepts `remaining_calls` parameter
   - Passes `remaining_calls` to form submit handler

## Usage Example

**User Input:**
```
"summarize photos and detect fakes in /tmp"
```

**Model Response:**
```json
<tool_code>{"name": "image_summary/summarize_images", "arguments": {"input_dir": "/tmp"}}</tool_code>
<tool_code>{"name": "deepfake_detection/give_prediction", "arguments": {"input_dataset": "/tmp"}}</tool_code>
```

**Execution Flow:**
1. User sees: "🔄 I'll process 2 task(s) sequentially:"
   - `1. image_summary/summarize_images`
   - `2. deepfake_detection/give_prediction`

2. **First Call:**
   - Form shown for `image_summary/summarize_images`
   - Input directory: `/tmp`
   - User can modify parameters
   - User submits → Job runs → Results shown

3. **Second Call (Automatic):**
   - Form shown for `deepfake_detection/give_prediction`
   - Input dataset: `/output/summaries` (chained from first call output)
   - User can modify if needed
   - User submits → Job runs → Results shown

4. **Both Results Visible:**
   - Both tool call results are visible in chat
   - User can scroll up to see first result
   - Both saved to history

## Output Chaining Logic

The system attempts to chain outputs by:

1. **Extracting output path** from previous ResponseBody:
   - `BatchDirectoryResponse.directories[0].path`
   - `DirectoryResponse.path`
   - Parent directory of `BatchFileResponse.files[0].path`
   - Parent directory of `FileResponse.path`

2. **Finding input directory field** in next schema:
   - Looks for input with `InputType.DIRECTORY`
   - Matches keys containing 'input' and 'dir' (case-insensitive)
   - Common patterns: `input_dir`, `input_directory`, `input_dataset`

3. **Updating arguments**:
   - Sets the input directory field to the extracted output path
   - Preserves other arguments from original tool call

## Error Handling

- **If a tool call fails**: Error is logged, but sequence continues with next call
- **If chaining fails**: Next call uses original arguments (no chaining)
- **If form loading fails**: Error shown, sequence stops

## Benefits

1. **Workflow Automation**: Complex multi-step workflows can be executed automatically
2. **Output Reuse**: No need to manually copy output paths between tools
3. **User Control**: Users can review and modify parameters at each step
4. **Result Visibility**: All results remain visible in chat history
5. **Backward Compatible**: Single tool calls work exactly as before

## Future Enhancements

Possible improvements:
- Auto-execution mode (skip forms, use model-provided arguments)
- Parallel execution for independent tool calls
- Result aggregation view (combine results from multiple calls)
- Workflow templates (save and replay common sequences)

