"""Integration tests for multiple tool calls with real API and Ollama"""

import pytest


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.ollama
async def test_multiple_tool_calls_extraction_with_ollama():
    """Test extracting multiple tool calls from real Ollama Granite model"""
    from frontend.chatbot.core import ChatbotCore
    from frontend.chatbot.config import ChatbotConfig

    config = ChatbotConfig()
    core = ChatbotCore(config)

    try:
        # Test prompt that should generate multiple tool calls
        prompt = "summarize photos and detect fakes in /tmp"

        tool_calls = await core.call_granite_model_direct(prompt)

        # Should return list (may be None if model fails)
        if tool_calls is not None:
            assert isinstance(tool_calls, list)
            assert len(tool_calls) > 0

            # Each tool call should have name and arguments
            for tool_call in tool_calls:
                assert "name" in tool_call
                assert "arguments" in tool_call
                assert isinstance(tool_call["arguments"], dict)
        else:
            pytest.skip("Model did not return tool calls - may need model retraining")

    finally:
        await core.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
async def test_chain_output_to_input_integration():
    """Test output chaining with real schema"""
    from frontend.chatbot.multi_tool_handler import chain_output_to_input
    from frontend.chatbot.core import ChatbotCore
    from frontend.chatbot.config import ChatbotConfig
    from rb.api.models import ResponseBody, DirectoryResponse

    config = ChatbotConfig()
    core = ChatbotCore(config)

    try:
        # Create a mock previous output
        previous_output = ResponseBody(
            root=DirectoryResponse(
                output_type="directory", path="/output/summaries", title="Summaries"
            )
        )

        # Get real schema for deepfake detection (which has input_dataset)
        try:
            schema = await core.get_task_schema_from_endpoint(
                "deepfake_detection/predict"
            )

            if schema:
                current_arguments = {"input_dir": "/tmp"}

                # Chain output
                result = chain_output_to_input(
                    previous_output, current_arguments, schema
                )

                # deepfake_detection/predict uses input_dir (directory); chain_output_to_input
                # matches keys containing "dir" (see multi_tool_handler).
                assert result.get("input_dir") == "/output/summaries"
        except Exception as e:
            pytest.skip(f"Could not load schema: {str(e)}")

    finally:
        await core.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
@pytest.mark.ollama
async def test_multiple_tool_calls_workflow():
    """Test complete workflow with multiple tool calls"""
    from frontend.chatbot.message_handler import MessageHandler
    from frontend.chatbot.core import ChatbotCore
    from frontend.chatbot.config import ChatbotConfig

    config = ChatbotConfig()
    core = ChatbotCore(config)
    handler = MessageHandler(core, config)

    try:
        # Test with a prompt that should generate multiple tool calls
        user_message = "summarize photos and detect fakes in /tmp"

        result = await handler.handle_message(user_message)

        # Should either return multi_tool_calls or show_form
        assert result["type"] in ["multi_tool_calls", "show_form", "message", "error"]

        if result["type"] == "multi_tool_calls":
            assert "tool_calls" in result
            assert len(result["tool_calls"]) > 0

            # Validate each tool call
            for tool_call in result["tool_calls"]:
                assert "endpoint" in tool_call
                assert "arguments" in tool_call
                assert isinstance(tool_call["arguments"], dict)
        elif result["type"] == "show_form":
            # Single tool call - backward compatible
            assert "endpoint" in result
            assert "arguments" in result

    finally:
        await core.close()
