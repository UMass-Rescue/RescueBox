"""
Unit tests for ChatbotCore functionality.

This module tests the core chatbot logic including task schema retrieval,
job submission, model interactions, and error handling. The tests focus
on the business logic layer, mocking external dependencies like APIs
and file systems.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.config import ChatbotConfig
from unittest.mock import AsyncMock


class TestUtilities:
    """Lightweight test utilities used by integration smoke tests."""

    @staticmethod
    def create_mock_chatbot_page():
        from unittest.mock import MagicMock
        chatbot = MagicMock()
        chatbot.state_manager = MagicMock()
        chatbot.state_manager.conversation_id = None
        chatbot.state_manager.messages = []
        return chatbot

    @staticmethod
    def create_mock_tool_registry():
        from unittest.mock import MagicMock
        return MagicMock()

    @staticmethod
    def create_mock_response_body():
        from unittest.mock import MagicMock
        return MagicMock()

    @staticmethod
    def create_mock_message_handler():
        from unittest.mock import MagicMock
        handler = MagicMock()
        handler.handle_message = AsyncMock(return_value={'type': 'message', 'content': 'ok'})
        return handler

    @staticmethod
    def create_mock_task_schema():
        from unittest.mock import MagicMock
        return MagicMock()


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
        mock_response.json = Mock(return_value=sample_task_schema.model_dump())
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
        mock_response.json = Mock(return_value={
            "response": f'<tool_code>{json.dumps(tool_call_json)}</tool_code>'
        })
        mock_response.raise_for_status = Mock()
        
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
        mock_response.json = Mock(return_value={
            "response": json.dumps(tool_call_json)
        })
        mock_response.raise_for_status = Mock()
        
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
        mock_response.json = Mock(return_value={
            "response": "No tool call here"
        })
        mock_response.raise_for_status = Mock()
        
        core.ollama_client.post = AsyncMock(return_value=mock_response)
        
        result = await core.call_granite_model("test prompt")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_call_granite_model_error(self, core):
        """Test Granite model call with error"""
        core.ollama_client.post = AsyncMock(side_effect=Exception("Connection error"))
        
        result = await core.call_granite_model("test prompt")
        
        assert result is None
    
    # Tests for call_granite_model_direct
    @pytest.mark.asyncio
    async def test_call_granite_model_direct_import_error(self, core):
        """Test call_granite_model_direct when llama-cpp-python is not installed"""
        # Patch the import statement inside the method to raise ImportError
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'llama_cpp':
                raise ImportError("No module named 'llama_cpp'")
            return original_import(name, *args, **kwargs)
        
        with patch.object(builtins, '__import__', side_effect=mock_import):
            result = await core.call_granite_model_direct("test prompt", use_advanced=True)
            assert result is None

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_file_not_found(self, core, tmp_path):
        """Test call_granite_model_direct when model file doesn't exist"""
        non_existent_path = tmp_path / "non_existent_model.gguf"
        
        with patch('llama_cpp.Llama', create=True):
            result = await core.call_granite_model_direct("test prompt", str(non_existent_path), use_advanced=True)
            assert result is None

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_success_tool_code_tags(self, core, tmp_path):
        """Test call_granite_model_direct with successful response containing tool_code tags"""
        import json
        from pathlib import Path
        
        # Create a mock model file
        model_file = tmp_path / "test_model.gguf"
        model_file.touch()
        
        tool_call_json = {
            "name": "audio/transcribe",
            "arguments": {"input_dir": "/tmp/audio"}
        }

        mock_response_text = f'<tool_code>{json.dumps(tool_call_json)}</tool_code>'

        # Mock the Llama model
        mock_model = MagicMock()
        mock_completion = {
            'choices': [{'message': {'content': mock_response_text}}]
        }
        mock_model.create_chat_completion.return_value = mock_completion
        
        with patch('llama_cpp.Llama', return_value=mock_model):
            with patch('llama_cpp.llama_supports_gpu_offload', return_value=False):
                with patch('pathlib.Path.exists', return_value=True):
                    import asyncio
                    # Create a mock loop that properly handles run_in_executor
                    mock_loop = MagicMock()
                    
                    async def mock_run_in_executor(executor, func, *args):
                        # Execute function immediately and return result
                        if args:
                            return func(*args)
                        return func()
                    
                    mock_loop.run_in_executor = mock_run_in_executor
                    
                    with patch('asyncio.get_event_loop', return_value=mock_loop):
                        result = await core.call_granite_model_direct("transcribe audio", str(model_file), use_advanced=False)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "audio/transcribe"
        assert result[0]["arguments"]["input_dir"] == "/tmp/audio"

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_success_json_fallback(self, core, tmp_path):
        """Test call_granite_model_direct with JSON fallback parsing"""
        import json
        from pathlib import Path
        
        # Create a mock model file
        model_file = tmp_path / "test_model.gguf"
        model_file.touch()
        
        tool_calls_data = {
            "calls": [
                {
                    "name": "image_summary/summarize-images",
                    "arguments": {"input_dir": "/tmp/images"}
                }
            ]
        }

        mock_response_content = json.dumps(tool_calls_data)

        # Mock the Llama model
        mock_model = MagicMock()
        mock_completion = {
            'choices': [{'message': {'content': mock_response_content}}]
        }
        mock_model.create_chat_completion.return_value = mock_completion
        
        with patch('llama_cpp.Llama', return_value=mock_model):
            with patch('llama_cpp.llama_supports_gpu_offload', return_value=False):
                with patch('pathlib.Path.exists', return_value=True):
                    import asyncio
                    mock_loop = MagicMock()
                    async def mock_run_in_executor(executor, func, *args):
                        if args:
                            return func(*args)
                        return func()
                    mock_loop.run_in_executor = mock_run_in_executor
                    
                    with patch('asyncio.get_event_loop', return_value=mock_loop):
                        result = await core.call_granite_model_direct("summarize images", str(model_file), use_advanced=True)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["name"] == "image_summary/summarize-images"
        assert result[0]["arguments"]["input_dir"] == "/tmp/images"
    
    @pytest.mark.asyncio
    async def test_call_granite_model_direct_multiple_tool_calls(self, core, tmp_path):
        """Test call_granite_model_direct with multiple tool calls"""
        import json
        from pathlib import Path
        
        # Create a mock model file
        model_file = tmp_path / "test_model.gguf"
        model_file.touch()
        
        tool_calls_data = {
            "calls": [
                {"name": "audio/transcribe", "arguments": {"input_dir": "/tmp/audio"}},
                {"name": "image_summary/summarize-images", "arguments": {"input_dir": "/tmp/images"}}
            ]
        }

        mock_response_content = json.dumps(tool_calls_data)

        # Mock the Llama model
        mock_model = MagicMock()
        mock_completion = {
            'choices': [{'message': {'content': mock_response_content}}]
        }
        mock_model.create_chat_completion.return_value = mock_completion
        
        with patch('llama_cpp.Llama', return_value=mock_model):
            with patch('llama_cpp.llama_supports_gpu_offload', return_value=False):
                with patch('pathlib.Path.exists', return_value=True):
                    import asyncio
                    mock_loop = MagicMock()
                    
                    async def mock_run_in_executor(executor, func, *args):
                        if args:
                            return func(*args)
                        return func()
                    
                    mock_loop.run_in_executor = mock_run_in_executor
                    
                    with patch('asyncio.get_event_loop', return_value=mock_loop):
                        result = await core.call_granite_model_direct("transcribe and summarize", str(model_file), use_advanced=True)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "audio/transcribe"
        assert result[1]["name"] == "image_summary/summarize-images"
    
    @pytest.mark.asyncio
    async def test_call_granite_model_direct_no_tool_call(self, core, tmp_path):
        """Test call_granite_model_direct when response contains no tool calls"""
        from pathlib import Path
        
        # Create a mock model file
        model_file = tmp_path / "test_model.gguf"
        model_file.touch()
        
        # Response with no tool calls - just regular text
        mock_response_content = "This is just regular text without any tool calls"

        # Mock the Llama model
        mock_model = MagicMock()
        mock_completion = {
            'choices': [{'message': {'content': mock_response_content}}]
        }
        mock_model.create_chat_completion.return_value = mock_completion
        
        with patch('llama_cpp.Llama', return_value=mock_model):
            with patch('llama_cpp.llama_supports_gpu_offload', return_value=False):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('asyncio.get_event_loop') as mock_loop:
                        def mock_run_in_executor(executor, func):
                            return func()
                        mock_loop.return_value.run_in_executor = lambda executor, func: func()

                        result = await core.call_granite_model_direct("test prompt", str(model_file), use_advanced=True)

        assert result is None

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_empty_response(self, core, tmp_path):
        """Test call_granite_model_direct when model returns empty response"""
        from pathlib import Path
        
        # Create a mock model file
        model_file = tmp_path / "test_model.gguf"
        model_file.touch()
        
        # Mock the Llama model with empty response
        mock_model = MagicMock()
        mock_completion = {
            'choices': []
        }
        mock_model.create_chat_completion.return_value = mock_completion
        
        with patch('llama_cpp.Llama', return_value=mock_model):
            with patch('llama_cpp.llama_supports_gpu_offload', return_value=False):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('asyncio.get_event_loop') as mock_loop:
                        def mock_run_in_executor(executor, func):
                            return func()
                        mock_loop.return_value.run_in_executor = lambda executor, func: func()

                        result = await core.call_granite_model_direct("test prompt", str(model_file), use_advanced=True)

        assert result is None

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_inference_error(self, core, tmp_path):
        """Test call_granite_model_direct when inference fails"""
        from pathlib import Path
        
        # Create a mock model file
        model_file = tmp_path / "test_model.gguf"
        model_file.touch()
        
        # Mock the Llama model to raise an error during inference
        mock_model = MagicMock()
        mock_model.create_chat_completion.side_effect = Exception("Inference error")
        
        with patch('llama_cpp.Llama', return_value=mock_model):
            with patch('llama_cpp.llama_supports_gpu_offload', return_value=False):
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('asyncio.get_event_loop') as mock_loop:
                        def mock_run_in_executor(executor, func):
                            return func()
                        mock_loop.return_value.run_in_executor = lambda executor, func: func()

                        result = await core.call_granite_model_direct("test prompt", str(model_file), use_advanced=True)

        assert result is None

    @pytest.mark.asyncio
    async def test_call_granite_model_direct_model_caching(self, core, tmp_path):
        """Test that call_granite_model_direct caches the model instance"""
        import json
        from pathlib import Path
        
        # Create a mock model file
        model_file = tmp_path / "test_model.gguf"
        model_file.touch()
        
        tool_calls_data = {
            "calls": [{"name": "audio/transcribe", "arguments": {}}]
        }
        mock_response_content = json.dumps(tool_calls_data)

        # Mock the Llama model
        mock_model = MagicMock()
        mock_completion = {
            'choices': [{'message': {'content': mock_response_content}}]
        }
        mock_model.create_chat_completion.return_value = mock_completion
        
        llama_constructor = MagicMock(return_value=mock_model)
        
        with patch('llama_cpp.Llama', llama_constructor):
            with patch('llama_cpp.llama_supports_gpu_offload', return_value=False):
                with patch('pathlib.Path.exists', return_value=True):
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Mock run_in_executor to execute function immediately
                    original_run_in_executor = loop.run_in_executor
                    def mock_run_in_executor(executor, func, *args):
                        # Execute function synchronously for testing
                        if args:
                            return func(*args)
                        return func()
                    loop.run_in_executor = mock_run_in_executor
                    
                    try:
                        # First call - should load model
                        result1 = await core.call_granite_model_direct("test prompt 1", str(model_file), use_advanced=True)
                        assert result1 is not None

                        # Second call - should reuse cached model
                        result2 = await core.call_granite_model_direct("test prompt 2", str(model_file), use_advanced=True)
                        assert result2 is not None
                        
                        # Llama constructor should only be called once (model caching)
                        assert llama_constructor.call_count == 1
                    finally:
                        # Restore original run_in_executor
                        loop.run_in_executor = original_run_in_executor
                        loop.close()

    @pytest.mark.asyncio
    async def test_close(self, core):
        """Test closing HTTP clients and llama model"""
        core.api_client.aclose = AsyncMock()
        core.ollama_client.aclose = AsyncMock()
        
        # Set up a mock llama model to test cleanup
        mock_llama_model = MagicMock()
        core._llama_model = mock_llama_model
        core._llama_model_path = "/path/to/model.gguf"
        
        await core.close()
        
        core.api_client.aclose.assert_called_once()
        core.ollama_client.aclose.assert_called_once()
        # Verify llama model is cleaned up
        assert core._llama_model is None
        assert core._llama_model_path is None

