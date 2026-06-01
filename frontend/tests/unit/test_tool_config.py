"""
Unit tests for tool configuration and management functionality.

This module tests the tool configuration system that manages available
processing tools, schema validation, and tool call parsing for the
RescueBox Assistant's advanced interaction capabilities.
"""

import pytest
import json
from pydantic import BaseModel
from frontend.chatbot.tool_config import (
    get_available_tools,
    update_tool_schema,
    remove_tool_schema,
    create_advanced_granite_prompt,
    parse_tool_calls_response,
    RescueBoxToolCall,
    ToolCallList
)

# Test constants
TEST_TOOL_NAME = "test/tool"
TEMP_TOOL_NAME = "temp/tool"
INVALID_TOOL_NAME = "invalid/tool"
TEST_PROMPT = "test prompt"
INVALID_JSON = "not json"


class TestToolConfiguration:
    """Test tool configuration management functions.

    This class tests the core tool configuration functionality including:
    - Tool registry management (add/remove tools)
    - Schema validation and updates
    - Advanced prompt generation for AI models
    - Tool call response parsing and validation
    """

    def test_get_available_tools(self):
        """Test retrieval of available tools registry.

        Verifies that the tool registry returns a properly structured
        dictionary containing all configured processing tools, with
        at least the basic audio transcription tool available.
        """
        tools = get_available_tools()
        assert isinstance(tools, dict)
        assert len(tools) > 0
        assert "audio/transcribe" in tools

    def test_update_tool_schema(self):
        """Test dynamic tool schema updates.

        Ensures that new tools can be registered with the system
        and their schemas properly stored and retrieved.
        """
        class TestTool(BaseModel):
            test_param: str = "test"

        # Register the test tool
        update_tool_schema(TEST_TOOL_NAME, TestTool)

        # Verify registration was successful
        tools = get_available_tools()
        assert TEST_TOOL_NAME in tools
        assert tools[TEST_TOOL_NAME] == TestTool

        # Clean up test data
        remove_tool_schema(TEST_TOOL_NAME)

    def test_remove_tool_schema(self):
        """Test tool schema removal functionality.

        Validates that registered tools can be properly removed from
        the system, ensuring clean cleanup and preventing stale tool
        definitions from persisting.
        """
        class TempTool(BaseModel):
            temp: str = "temp"

        # Register and verify tool exists
        update_tool_schema(TEMP_TOOL_NAME, TempTool)
        assert TEMP_TOOL_NAME in get_available_tools()

        # Remove and verify cleanup
        remove_tool_schema(TEMP_TOOL_NAME)
        assert TEMP_TOOL_NAME not in get_available_tools()

    def test_create_advanced_granite_prompt(self):
        """Test advanced prompt generation for Granite model.

        Verifies that the prompt generation system creates properly
        structured message sequences with system context and tool
        definitions, preparing the AI model for advanced tool usage.
        """
        messages = create_advanced_granite_prompt(TEST_PROMPT)

        assert isinstance(messages, list)
        assert len(messages) >= 2  # At least system + user message

        # Validate system message structure and content
        system_msg = messages[0]
        assert system_msg["role"] == "system"
        assert "RescueBox" in system_msg["content"]
        assert "<tools>" in system_msg["content"]

        # Validate user message content
        user_msg = messages[-1]
        assert user_msg["role"] == "user"
        assert user_msg["content"] == TEST_PROMPT

    def test_parse_tool_calls_response_valid(self):
        """Test parsing of valid tool call responses.

        Ensures that properly formatted JSON tool call responses are
        correctly parsed into structured tool call objects that can
        be executed by the system.
        """
        valid_content = json.dumps({
            "calls": [
                {
                    "name": "audio/transcribe",
                    "arguments": {"input_dir": "/test/path"}
                }
            ]
        })

        result = parse_tool_calls_response(valid_content)

        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "audio/transcribe"
        assert result[0]["arguments"]["input_dir"] == "/test/path"

    def test_parse_tool_calls_response_invalid(self):
        """Test handling of malformed tool call responses.

        Validates that invalid or non-JSON responses are handled gracefully
        without causing system crashes, returning None for unparseable input.
        """
        result = parse_tool_calls_response(INVALID_JSON)
        assert result is None

    def test_rescue_box_tool_call_validation(self):
        """Test RescueBoxToolCall model validation.

        Ensures that tool call objects enforce proper validation rules,
        accepting only registered tool names and properly structured arguments.
        """
        # Valid tool call should work without issues
        valid_call = RescueBoxToolCall(
            name="audio/transcribe",
            arguments={"input_dir": "/test"}
        )
        assert valid_call.name == "audio/transcribe"
        assert valid_call.arguments["input_dir"] == "/test"

        # Invalid tool names should be rejected
        with pytest.raises(ValueError):
            RescueBoxToolCall(
                name=INVALID_TOOL_NAME,
                arguments={}
            )

    def test_tool_call_list_validation(self):
        """Test ToolCallList batch validation.

        Validates that collections of tool calls can be properly validated
        and structured for batch processing operations.
        """
        tool_calls = [
            RescueBoxToolCall(name="audio/transcribe", arguments={"input_dir": "/test1"}),
            RescueBoxToolCall(name="text_summarization/summarize", arguments={
                "input_dir": "/test2",
                "output_dir": "/output",
                "model": "gemma3:1b"
            })
        ]

        tool_list = ToolCallList(calls=tool_calls)
        assert len(tool_list.calls) == 2
        assert tool_list.calls[0].name == "audio/transcribe"
        assert tool_list.calls[1].name == "text_summarization/summarize"
