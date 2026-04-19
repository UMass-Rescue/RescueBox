"""
Unit tests for ChatbotCore functionality.

This module tests the core chatbot logic including task schema retrieval,
job submission, model interactions, and error handling. The tests focus
on the business logic layer, mocking external dependencies like APIs
and file systems.
"""

import pytest
import httpx
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.config import ChatbotConfig


class TestChatbotCore:
    """Tests for ChatbotCore class.

    This class tests the core chatbot functionality including:
    - Task schema retrieval from endpoints
    - Job submission and processing
    - Model interactions (Granite, Ollama)
    - Error handling and recovery
    - Configuration management
    """

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ChatbotConfig()

    @pytest.fixture
    def core(self, config, mock_api_client):
        """Create ChatbotCore instance with mocked dependencies."""
        core = ChatbotCore(config)
        # Mock external dependencies
        core.api_client = mock_api_client
        core.ollama_client = AsyncMock()
        return core
    
    @pytest.mark.asyncio
    async def test_get_task_schema_from_endpoint_success(self, core, sample_task_schema):
        """Test successful task schema retrieval from endpoint.

        Verifies that the core can successfully fetch and parse
        a task schema from an external API endpoint, handling
        the HTTP response correctly and returning a valid TaskSchema.
        """
        from rb.api.models import TaskSchema

        mock_response = Mock()
        mock_response.json.return_value = sample_task_schema.model_dump()
        mock_response.raise_for_status = Mock()

        with patch('httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client.get = Mock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            schema = await core.get_task_schema_from_endpoint("audio/transcribe")

            assert isinstance(schema, TaskSchema)
            assert len(schema.inputs) == 2
            mock_client.get.assert_called_once_with("/audio/transcribe/task_schema")
    
    @pytest.mark.asyncio
    async def test_get_task_schema_from_endpoint_with_slash(self, core, sample_task_schema):
        """Test schema retrieval handles endpoints with leading slashes.

        Ensures that endpoints provided with or without leading slashes
        are handled consistently, preventing double-slash issues in URLs.
        """
        from rb.api.models import TaskSchema

        mock_response = Mock()
        mock_response.json = Mock(return_value=sample_task_schema.model_dump())
        mock_response.raise_for_status = Mock()

        with patch('httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client.get = Mock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            schema = await core.get_task_schema_from_endpoint("/audio/transcribe")

            assert isinstance(schema, TaskSchema)
            # Should call with /audio/transcribe/task_schema (no double slash)
            call_args = mock_client.get.call_args[0][0]
            assert call_args == "/audio/transcribe/task_schema"
    
    @pytest.mark.asyncio
    async def test_get_task_schema_from_endpoint_error(self, core):
        """Test schema retrieval handles HTTP errors gracefully.

        Verifies that network errors and HTTP status errors are
        properly caught and re-raised as meaningful exceptions,
        allowing the application to handle API failures appropriately.
        """
        import httpx

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        ))

        with patch('httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client.get = Mock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(Exception, match="Endpoint not found"):
                await core.get_task_schema_from_endpoint("audio/transcribed")
    
    def test_convert_arguments_to_initial_values(self, core, sample_task_schema):
        """Test argument conversion to initial values"""
        arguments = {
            "input_dir": "/tmp/test",
            "prompt": "test prompt",
            "confidence": 0.9
        }
        
        initial_values = core.convert_arguments_to_initial_values(
            arguments, sample_task_schema, endpoint="audio/transcribe"
        )
        
        assert "inputs" in initial_values
        assert "parameters" in initial_values
        assert "input_dir" in initial_values["inputs"]
        assert initial_values["inputs"]["input_dir"]["path"] == "/tmp/test"
        assert initial_values["inputs"]["prompt"]["text"] == "test prompt"
        assert initial_values["parameters"]["confidence"] == 0.9
    
    def test_convert_arguments_normalizes_keys(self, core, sample_task_schema):
        """Test that argument conversion normalizes keys"""
        arguments = {
            "input_directory": "/tmp/test",  # Should normalize to input_dir
            "prompt": "test"
        }
        
        initial_values = core.convert_arguments_to_initial_values(
            arguments, sample_task_schema, endpoint="audio/transcribe"
        )
        
        # Should normalize input_directory to input_dir
        assert "input_dir" in initial_values["inputs"]

    def test_convert_arguments_unwraps_nested_text_dict(self, core):
        """UFDR mount_name sometimes arrives as {'text': '/tmp/x'}; do not str() the dict."""
        from rb.api.models import TaskSchema, InputSchema, InputType

        schema = TaskSchema(
            inputs=[
                InputSchema(key="mount_name", label="Mount", input_type=InputType.TEXT),
            ],
            parameters=[],
        )
        initial_values = core.convert_arguments_to_initial_values(
            {"mount_name": {"text": "/tmp/case3"}},
            schema,
            endpoint="ufdr_mounter/mount",
        )
        assert initial_values["inputs"]["mount_name"]["text"] == "/tmp/case3"

    def test_convert_arguments_preserves_image_search_query(self, core):
        """Granite tool args include ``query``; form pre-fill must not drop the phrase."""
        from rb.api.models import TaskSchema, InputSchema, InputType

        schema = TaskSchema(
            inputs=[
                InputSchema(
                    key="input_dir",
                    label="Images",
                    input_type=InputType.DIRECTORY,
                ),
                InputSchema(
                    key="query",
                    label="Search",
                    input_type=InputType.TEXT,
                ),
            ],
            parameters=[],
        )
        initial_values = core.convert_arguments_to_initial_values(
            {"input_dir": "/data/evidence/photos", "query": "food"},
            schema,
            endpoint="image_embeddings/search_images",
        )
        assert initial_values["inputs"]["query"]["text"] == "food"

    @pytest.mark.asyncio
    async def test_submit_job_success(self, core):
        """Test successful job submission"""
        import httpx
        from rb.api.models import RequestBody, DirectoryInput, TextInput, ResponseBody, TextResponse

        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={
                    "input_dir": DirectoryInput(path=Path(temp_dir)),
                    "prompt": TextInput(text="test")
                },
                parameters={}
            )

            mock_response = Mock()
            mock_response.json = Mock(return_value={
                "root": {
                    "output_type": "text",
                    "value": "Job completed"
                }
            })
            mock_response.raise_for_status = Mock()

            with patch('httpx.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.__enter__ = Mock(return_value=mock_client)
                mock_client.__exit__ = Mock(return_value=None)
                mock_client.post = Mock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                response = await core.submit_job(request_body, "audio/transcribe")

                assert isinstance(response, ResponseBody)
                mock_client.post.assert_called_once_with("/audio/transcribe", json={
                    'inputs': {'input_dir': {'path': temp_dir}, 'prompt': {'text': 'test'}},
                    'parameters': {}
                })
    
    @pytest.mark.asyncio
    async def test_call_granite_model_success(self, core):
        """Test successful Granite model call"""
        import json
        
        tool_call_json = {
            "name": "audio/transcribe",
            "arguments": {"input_dir": "/tmp"}
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={
            "message": {"content": f'<tool_code>{json.dumps(tool_call_json)}</tool_code>'},
        })
        
        core.ollama_client.post = AsyncMock(return_value=mock_response)
        
        result = await core.call_granite_model("test prompt")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["name"] == "audio/transcribe"
        assert "input_dir" in result[0]["arguments"]
    
    @pytest.mark.asyncio
    async def test_call_granite_model_fallback_json(self, core):
        """Test Granite model call with fallback JSON parsing"""
        import json
        
        tool_call_json = {
            "name": "audio/transcribe",
            "arguments": {"input_dir": "/tmp"}
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={
            "message": {"content": json.dumps(tool_call_json)},
        })
        
        core.ollama_client.post = AsyncMock(return_value=mock_response)
        
        result = await core.call_granite_model("test prompt")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["name"] == "audio/transcribe"
    
    @pytest.mark.asyncio
    async def test_call_granite_model_no_tool_call(self, core):
        """Test Granite model call with no tool call in response"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"message": {"content": "No tool call here"}})
        
        core.ollama_client.post = AsyncMock(return_value=mock_response)
        
        result = await core.call_granite_model("test prompt")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_call_granite_model_error(self, core):
        """Test Granite model call with error"""
        core.ollama_client.post = AsyncMock(side_effect=Exception("Connection error"))
        
        result = await core.call_granite_model("test prompt")
        
        assert result is None
    
    # Tests for call_granite_model_direct (Ollama /api/chat)
    @staticmethod
    def _ollama_ok(content: str):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"message": {"content": content}})
        return mock_response

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_success_tool_code_tags(self, core):
        """Ollama returns tool calls in message.content inside <tool_code> tags."""
        import json

        tool_call_json = {"name": "audio/transcribe", "arguments": {"input_dir": "/tmp/audio"}}
        content = f'<tool_code>{json.dumps(tool_call_json)}</tool_code>'
        core.ollama_client.post = AsyncMock(return_value=self._ollama_ok(content))

        result = await core.call_granite_model_direct("transcribe audio", use_advanced=False)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "audio/transcribe"
        assert result[0]["arguments"]["input_dir"] == "/tmp/audio"

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_success_json_fallback(self, core):
        """Ollama returns JSON with calls array in message.content."""
        import json

        tool_calls_data = {
            "calls": [{"name": "image_summary/summarize-images", "arguments": {"input_dir": "/tmp/images"}}]
        }
        core.ollama_client.post = AsyncMock(return_value=self._ollama_ok(json.dumps(tool_calls_data)))

        result = await core.call_granite_model_direct("summarize images", use_advanced=True)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["name"] == "image_summary/summarize-images"
        assert result[0]["arguments"]["input_dir"] == "/tmp/images"

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_multiple_tool_calls(self, core):
        import json

        tool_calls_data = {
            "calls": [
                {"name": "audio/transcribe", "arguments": {"input_dir": "/tmp/audio"}},
                {"name": "image_summary/summarize-images", "arguments": {"input_dir": "/tmp/images"}},
            ]
        }
        core.ollama_client.post = AsyncMock(return_value=self._ollama_ok(json.dumps(tool_calls_data)))

        result = await core.call_granite_model_direct("transcribe and summarize", use_advanced=True)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "audio/transcribe"
        assert result[1]["name"] == "image_summary/summarize-images"

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_no_tool_call(self, core):
        core.ollama_client.post = AsyncMock(
            return_value=self._ollama_ok("This is just regular text without any tool calls")
        )
        result = await core.call_granite_model_direct("test prompt", use_advanced=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_empty_response(self, core):
        core.ollama_client.post = AsyncMock(return_value=self._ollama_ok(""))
        result = await core.call_granite_model_direct("test prompt", use_advanced=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_inference_error(self, core):
        core.ollama_client.post = AsyncMock(side_effect=httpx.RequestError("Inference transport error"))
        result = await core.call_granite_model_direct("test prompt", use_advanced=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_model_caching(self, core):
        """Each call hits Ollama; no local GGUF cache."""
        import json

        payload = json.dumps({"calls": [{"name": "audio/transcribe", "arguments": {}}]})
        mock_post = AsyncMock(return_value=self._ollama_ok(payload))
        core.ollama_client.post = mock_post

        result1 = await core.call_granite_model_direct("test prompt 1", use_advanced=True)
        result2 = await core.call_granite_model_direct("test prompt 2", use_advanced=True)
        assert result1 is not None
        assert result2 is not None
        assert mock_post.await_count == 2

    @pytest.mark.asyncio
    async def test_close(self, core):
        """Test closing HTTP clients and llama model"""
        core.api_client.aclose = AsyncMock()
        core.ollama_client.aclose = AsyncMock()
        core.api.aclose = AsyncMock()

        # Set up legacy attribute to test cleanup
        core._llama_model = MagicMock()

        await core.close()

        core.api_client.aclose.assert_called_once()
        core.ollama_client.aclose.assert_called_once()
        core.api.aclose.assert_called_once()
        assert core._llama_model is None

