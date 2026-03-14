# Advanced Tool Configuration System

This document describes the modular tool configuration system for RescueBox's chatbot, with both advanced and legacy approaches available.

## Overview

The tool configuration system provides two approaches:

- **Modular Design**: Tool schemas and configuration separated from core business logic
- **Runtime Configurability**: Tools can be added, modified, or removed at runtime
- **Advanced Prompting**: Few-shot learning for intelligent multi-tool chaining
- **Strict Validation**: Pydantic schemas ensure data integrity
- **Backward Compatibility**: Legacy support for existing implementations

## Architecture

### Core Components

1. **Tool Schemas** (`TextSummarize`, `ImageSummarize`, etc.)
   - Pydantic models defining tool parameters
   - Strict validation with type hints and constraints
   - Rich metadata (descriptions, defaults, literals)

2. **Router Schema** (`RescueBoxToolCall`, `ToolCallList`)
   - Structured output format for AI model responses
   - Validation of tool calls and arguments
   - Type-safe parsing from JSON responses

3. **Configuration System** (`SCHEMA_MAP`, management functions)
   - Runtime-editable tool registry
   - Dynamic schema generation
   - Hot-swappable configurations

## Usage

### Basic Tool Management

```python
from frontend.chatbot.tool_config import (
    get_available_tools,
    update_tool_schema,
    remove_tool_schema
)

# Get current tools
tools = get_available_tools()
print(f"Available tools: {list(tools.keys())}")

# Add a new tool
from pydantic import BaseModel

class MyCustomTool(BaseModel):
    input_path: str
    output_path: str = "/default/output"

update_tool_schema("my-custom/tool", MyCustomTool)

# Remove a tool
remove_tool_schema("old/tool")
```

### Advanced Prompting

```python
from frontend.chatbot.tool_config import create_advanced_granite_prompt

# Create intelligent prompt with few-shot examples
messages = create_advanced_granite_prompt("transcribe audio and detect deepfakes in /evidence")

# This generates a comprehensive prompt that teaches the AI:
# - How to chain multiple tools
# - How to distribute paths across tools
# - How to infer missing parameters
# - Pattern recognition from examples
```

### Response Parsing

```python
from frontend.chatbot.tool_config import parse_tool_calls_response

# Parse AI model response
response_json = '{"calls": [{"name": "audio/transcribe", "arguments": {"input_dir": "/test"}}]}'
tool_calls = parse_tool_calls_response(response_json)

# Returns validated tool call dictionaries
# [{"name": "audio/transcribe", "arguments": {"input_dir": "/test"}}]
```

## Available Tools

| Tool Name | Schema Class | Description |
|-----------|--------------|-------------|
| `audio/transcribe` | `AudioTranscribe` | Audio transcription service |
| `age-gender/predict` | `AgeGenderPredict` | Age/gender prediction from images |
| `text_summarization/summarize` | `TextSummarize` | Text summarization with model selection |
| `image_summary/summarize-images` | `ImageSummarize` | Image content summarization |
| `face-match/findfacebulk` | `FaceFindBulk` | Bulk face matching with similarity |
| `face-match/bulkupload` | `FaceBulkUpload` | Bulk face database upload |
| `deepfake_detection/predict` | `DeepfakeDetection` | Deepfake detection and reporting |

## Dual Approach Availability

The system maintains both advanced and legacy approaches for maximum flexibility:

### Advanced Approach (Default)
- Comprehensive tool set with intelligent chaining
- Few-shot prompting for complex multi-tool requests
- Structured JSON output with Pydantic validation

### Legacy Approach (Backward Compatibility)
- Simple audio transcription only
- Basic `<tool_code>` tag parsing
- Minimal dependencies and complexity

## Approach Comparison

| Feature | Advanced Approach | Legacy Approach |
|---------|------------------|-----------------|
| **Tool Support** | 7 comprehensive tools | 1 tool (audio/transcribe) |
| **Multi-tool Chaining** | ✅ Intelligent chaining | ❌ Single tool only |
| **Prompting** | Few-shot with examples | Simple system message |
| **Output Format** | Structured JSON schema | Free-form with `<tool_code>` |
| **Validation** | Pydantic model validation | Basic JSON parsing |
| **Configuration** | Runtime editable | Hardcoded |
| **Use Case** | Complex forensic workflows | Simple audio transcription |

## Integration with Core

The tool configuration system integrates seamlessly with `ChatbotCore`:

```python
from frontend.chatbot.core import ChatbotCore

core = ChatbotCore(config)

# Access tool schemas directly from tool_config
from frontend.chatbot.tool_config import get_available_tools, update_tool_schema, remove_tool_schema

schemas = get_available_tools()

# Generate tool definitions directly
from frontend.chatbot.tool_config import generate_tool_definitions
definitions = generate_tool_definitions()

# Modify tool configuration
update_tool_schema("new/tool", NewToolSchema)
remove_tool_schema("old/tool")

# Call Granite model with different approaches
tool_calls = await core.call_granite_model_direct("transcribe audio")  # Advanced (default)
tool_calls = await core.call_granite_model_direct("transcribe audio", use_advanced=False)  # Legacy
tool_calls = await core.call_granite_model_direct_legacy("transcribe audio")  # Legacy (convenience)
```

## Advanced Features

### Few-Shot Prompting

The system uses sophisticated few-shot prompting to teach the AI:

1. **Pattern A**: Path at start, distribute forward
   - Input: "In /cases/c10, summarize text and check for deepfakes"
   - Output: Multiple tools using same path

2. **Pattern B**: Path at end, distribute backward
   - Input: "Summarize images and detect fakes in /evidence/batch2"
   - Output: Multiple tools using same path

3. **Pattern C**: Chain of 3+ tools
   - Input: "Transcribe audio, then detect fakes and summarize images in /data"
   - Output: Sequential tool execution with context sharing

### Dynamic Schema Generation

Tool definitions are generated dynamically from Pydantic schemas:

```python
# Automatically creates OpenAI-compatible function definitions
{
    "type": "function",
    "function": {
        "name": "audio/transcribe",
        "description": "Path to input audio",
        "parameters": {
            "type": "object",
            "properties": {
                "input_dir": {"type": "string", "description": "..."}
            },
            "required": ["input_dir"]
        }
    }
}
```

### Validation & Type Safety

All tool calls are validated using Pydantic:

```python
# This will raise ValidationError if invalid
tool_call = RescueBoxToolCall(
    name="invalid/tool",  # Not in allowed literals
    arguments={"invalid": "params"}
)
```

## Migration Guide

### From Legacy Approach

**Old way** (hardcoded in core.py):
```python
# Hardcoded tool definitions
tool = {"type": "function", "function": {...}}
```

**New way** (modular configuration):
```python
# Dynamic from schema map
from frontend.chatbot.tool_config import generate_tool_definitions
tools = generate_tool_definitions()
```

### Benefits of New Approach

1. **Maintainability**: Tool configuration separate from business logic
2. **Extensibility**: Add tools without modifying core files
3. **Testability**: Isolated testing of tool configuration
4. **Flexibility**: Runtime tool management
5. **Validation**: Strict type checking and validation

## Testing

Run the tool configuration tests:

```bash
pytest frontend/tests/unit/test_tool_config.py -v
```

Tests cover:
- Tool schema management
- Prompt generation
- Response parsing
- Validation
- Error handling

## Future Enhancements

- Tool versioning and migration
- Tool dependency management
- Performance profiling per tool
- A/B testing of prompt variations
- Tool recommendation system
