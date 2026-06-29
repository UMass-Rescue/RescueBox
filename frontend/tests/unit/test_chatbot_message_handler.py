"""
Unit tests for MessageHandler functionality.

This module tests the message processing and routing logic that determines
how user input is interpreted and handled, including slash commands,
smart analysis requests, and message formatting for different output types.
"""

import pytest
from unittest.mock import AsyncMock, patch
from frontend.chatbot.message_handler import MessageHandler


class TestMessageHandler:
    """Tests for MessageHandler class.

    This class tests the core message processing functionality including:
    - Input method detection (slash commands vs smart analysis)
    - Slash command processing and responses
    - Message formatting and display
    - Error handling in message processing
    """

    @pytest.fixture
    def handler(self, mock_chatbot):
        """Create MessageHandler instance with mocked dependencies."""
        from frontend.chatbot.config import ChatbotConfig

        config = ChatbotConfig()
        return MessageHandler(mock_chatbot, config)

    def test_detect_input_method_slash_command(self, handler):
        """Test detection of slash command input method.

        Verifies that messages starting with '/' are correctly identified
        as slash commands, which trigger specific command processing logic.
        """
        method = handler.detect_input_method("/transcribe")
        assert method == "slash_command"

    def test_detect_input_method_smart_analyze(self, handler):
        """Test detection of smart analysis input method.

        Ensures that natural language requests for analysis are properly
        identified and routed to the smart analysis processing pipeline.
        """
        method = handler.detect_input_method("transcribe audio files")
        assert method == "smart_analyze"

    def test_detect_input_method_whitespace(self, handler):
        """Test input method detection handles whitespace correctly.

        Validates that leading and trailing whitespace is properly trimmed
        before input method detection, ensuring consistent behavior.
        """
        method = handler.detect_input_method("  /transcribe  ")
        assert method == "slash_command"

    @pytest.mark.asyncio
    async def test_handle_slash_command_help(self, handler):
        """Test processing of /help slash command.

        Verifies that the help command returns appropriate guidance
        and information about the RescueBox Assistant's capabilities.
        """
        result = await handler.handle_slash_command("/help")

        assert result["type"] == "help"
        assert "RescueBox Assistant" in result["content"]

    @pytest.mark.asyncio
    async def test_handle_slash_command_tools(self, handler):
        """Test processing of /models slash command.

        Ensures that the models command triggers the tool picker interface,
        allowing users to select from available processing tools.
        """
        result = await handler.handle_slash_command("/models")

        assert result["type"] == "tool_picker"

    @pytest.mark.asyncio
    async def test_handle_slash_command_analyze(self, handler):
        """Test processing of /assistant slash command (smart analyze routing)."""
        # Mock the smart analyze handler to return expected response
        handler.handle_smart_analyze = AsyncMock(
            return_value={
                "type": "show_form",
                "endpoint": "audio/transcribed",
                "arguments": {},
            }
        )

        result = await handler.handle_slash_command("/assistant transcribe audio")

        assert result["type"] == "show_form"
        handler.handle_smart_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_slash_command_analyze_with_filter(self, handler):
        """Test /assistant command with filtering enabled"""
        handler.config.FILTER_ENABLED = True

        # Mock is_rescuebox_request to return invalid
        with patch(
            "frontend.chatbot.message_handler.is_rescuebox_request"
        ) as mock_filter:
            mock_filter.return_value = (False, "non_forensic")

            result = await handler.handle_slash_command("/assistant tell me a joke")

            assert result["type"] == "message"
            assert result["content"]

    @pytest.mark.asyncio
    async def test_handle_slash_command_valid_tool(self, handler):
        """Test handling valid slash command"""
        result = await handler.handle_slash_command("/transcribe")

        assert result["type"] == "show_form"
        assert result["endpoint"] == "audio/transcribe"
        assert result["arguments"] == {}

    @pytest.mark.asyncio
    async def test_handle_slash_command_invalid(self, handler):
        """Test handling invalid slash command"""
        result = await handler.handle_slash_command("/invalid")

        assert result["type"] == "error"
        assert "Unknown command" in result["content"]

    @pytest.mark.asyncio
    async def test_handle_smart_analyze_success(self, handler):
        """Test successful smart analyze"""
        tool_call = [{"name": "audio/transcribed", "arguments": {"input_dir": "/tmp"}}]

        with patch.object(
            handler.core, "call_granite_model_direct", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = tool_call
            with patch.object(
                handler.core, "get_task_schema_from_endpoint", return_value=None
            ):
                result = await handler.handle_smart_analyze("transcribe audio files")

                assert result["type"] == "show_form"
                assert result["endpoint"] == "audio/transcribed"
                assert "input_dir" in result["arguments"]

    @pytest.mark.asyncio
    async def test_handle_smart_analyze_with_filtering(self, handler):
        """Test smart analyze with filtering enabled"""
        handler.config.FILTER_ENABLED = True

        # Mock filter to reject
        with patch(
            "frontend.chatbot.message_handler.is_rescuebox_request"
        ) as mock_filter:
            mock_filter.return_value = (False, "non_forensic")
            with patch.object(
                handler.core, "call_granite_model_direct", new_callable=AsyncMock
            ) as mock_call:
                result = await handler.handle_smart_analyze("tell me a joke")

                assert result["type"] == "message"
                assert "RescueBox chat Assistant" in result["content"]
                # Should not call Granite model
                mock_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_smart_analyze_no_tool_call(self, handler):
        """Test smart analyze when Granite model returns no tool call"""
        with patch.object(
            handler.core, "call_granite_model_direct", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = None

            result = await handler.handle_smart_analyze("transcribe audio")

            assert result["type"] == "message"
        assert "Could not determine" in result["content"]

    @pytest.mark.asyncio
    async def test_handle_smart_analyze_missing_endpoint(self, handler):
        """Test smart analyze with missing endpoint in tool call"""
        tool_call = [{"arguments": {"input_dir": "/tmp"}}]  # Missing 'name' field

        with patch.object(
            handler.core, "call_granite_model_direct", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = tool_call

            result = await handler.handle_smart_analyze("transcribe audio")

            # When no valid tool calls are found (missing name field), it returns an error type
            assert result["type"] == "error"
            assert "No valid tool calls" in result["content"]

    @pytest.mark.asyncio
    async def test_handle_smart_analyze_normalizes_arguments(self, handler):
        """Test that smart analyze normalizes arguments"""
        tool_call = [
            {
                "name": "audio/transcribed",
                "arguments": {
                    "input_directory": "/tmp"
                },  # Should normalize to input_dir
            }
        ]

        # Use input that will pass filtering, or disable filtering
        # "transcribe audio" contains keyword "transcribe" so it will pass the filter
        test_input = "transcribe audio"

        with patch.object(
            handler.core, "call_granite_model_direct", new_callable=AsyncMock
        ) as mock_call:
            mock_call.return_value = tool_call

            result = await handler.handle_smart_analyze(test_input)

            # Verify mock was called
            mock_call.assert_called_once()

            # Arguments should be normalized and return show_form for single tool call
            assert result["type"] == "show_form"
            assert result["endpoint"] == "audio/transcribed"
            # Arguments should be normalized (input_directory -> input_dir)
            assert "input_dir" in result["arguments"]
            # normalize_arguments should be called (checked via integration)

    @pytest.mark.asyncio
    async def test_handle_message_routes_to_slash_command(self, handler):
        """Test message routing to slash command handler"""
        handler.handle_slash_command = AsyncMock(return_value={"type": "help"})

        result = await handler.handle_message("/help")

        assert result["type"] == "help"
        handler.handle_slash_command.assert_called_once_with("/help", None)

    @pytest.mark.asyncio
    async def test_handle_message_routes_to_smart_analyze(self, handler):
        """Test message routing to smart analyze handler"""
        handler.handle_smart_analyze = AsyncMock(return_value={"type": "show_form"})

        result = await handler.handle_message("transcribe audio")

        assert result["type"] == "show_form"
        handler.handle_smart_analyze.assert_called_once_with("transcribe audio", None)
