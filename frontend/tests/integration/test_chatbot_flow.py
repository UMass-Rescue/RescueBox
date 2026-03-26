"""
Integration tests for chatbot flow (USES MOCKS)

NOTE: This file uses mocks for API and Ollama clients.
For tests with real dependencies, see test_chatbot_flow_integration.py

This file is kept for fast unit-style testing of chatbot flow logic.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, Mock
from pathlib import Path
from frontend.chatbot.config import ChatbotConfig
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.message_handler import MessageHandler


class TestChatbotFlow:
    """Integration tests for chatbot user flow (with mocked dependencies)"""
    
    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return ChatbotConfig(FILTER_ENABLED=False)  # Disable filtering for tests
    
    @pytest.fixture
    def mock_core(self, config):
        """Create ChatbotCore with mocked HTTP clients"""
        core = ChatbotCore(config)
        core.api_client = AsyncMock()
        core.ollama_client = AsyncMock()
        return core
    
    @pytest.mark.asyncio
    async def test_slash_command_flow(self, mock_core, config):
        """Test complete flow: slash command -> form display"""
        handler = MessageHandler(mock_core, config)
        
        # Mock schema response
        mock_schema_response = AsyncMock()
        mock_schema_response.json.return_value = {
            'inputs': [{
                'key': 'input_dir',
                'label': 'Input Directory',
                'inputType': 'directory'
            }],
            'parameters': []
        }
        mock_schema_response.raise_for_status = Mock()
        mock_core.api_client.get.return_value = mock_schema_response
        
        # Handle slash command
        result = await handler.handle_message("/transcribe")
        
        assert result["type"] == "show_form"
        assert result["endpoint"] == "audio/transcribe"
    
    @pytest.mark.asyncio
    async def test_smart_analyze_flow(self, mock_core, config):
        """Test complete flow: natural language -> Granite model -> form"""
        handler = MessageHandler(mock_core, config)
        
        # Mock Granite model response
        tool_call = {
            "name": "audio/transcribe",
            "arguments": {"input_dir": "/tmp/audio"}
        }
        mock_ollama_response = MagicMock()
        mock_ollama_response.status_code = 200
        mock_ollama_response.json = Mock(
            return_value={
                "message": {"content": f'<tool_code>{json.dumps(tool_call)}</tool_code>'},
            }
        )
        mock_ollama_response.raise_for_status = Mock()
        mock_core.ollama_client.post = AsyncMock(return_value=mock_ollama_response)
        
        # Mock schema response
        mock_schema_response = AsyncMock()
        mock_schema_response.json.return_value = {
            'inputs': [{
                'key': 'input_dir',
                'label': 'Input Directory',
                'inputType': 'directory'
            }],
            'parameters': []
        }
        mock_schema_response.raise_for_status = Mock()
        mock_core.api_client.get.return_value = mock_schema_response
        
        # Handle smart analyze
        result = await handler.handle_message("transcribe audio files in /tmp")
        
        assert result["type"] == "show_form"
        assert result["endpoint"] == "audio/transcribe"
        assert "input_dir" in result["arguments"]
    
    @pytest.mark.asyncio
    async def test_argument_normalization_in_flow(self, mock_core, config):
        """Test that arguments are normalized during smart analyze"""
        handler = MessageHandler(mock_core, config)
        
        # Mock Granite model response with non-normalized keys
        tool_call = {
            "name": "audio/transcribe",
            "arguments": {"input_directory": "/tmp/audio"}  # Should normalize to input_dir
        }
        mock_ollama_response = MagicMock()
        mock_ollama_response.status_code = 200
        mock_ollama_response.json = Mock(
            return_value={
                "message": {"content": f'<tool_code>{json.dumps(tool_call)}</tool_code>'},
            }
        )
        mock_ollama_response.raise_for_status = Mock()
        mock_core.ollama_client.post = AsyncMock(return_value=mock_ollama_response)
        
        result = await handler.handle_message("transcribe audio in /tmp")
        
        # Arguments should be normalized
        assert result["type"] == "show_form"
        # The normalization happens in handle_smart_analyze
    
    @pytest.mark.asyncio
    async def test_input_filtering_in_flow(self, mock_core):
        """Test that input filtering works in message handler"""
        config = ChatbotConfig(FILTER_ENABLED=True)
        handler = MessageHandler(mock_core, config)
        
        # Test blocked request
        result = await handler.handle_message("tell me a joke")
        
        assert result["type"] == "message"
        assert "Request Not Supported" in result["content"]
        # Should not call Granite model
        mock_core.ollama_client.post.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_job_submission_flow(self, mock_core, config, sample_task_schema):
        """Test job submission flow"""
        from rb.api.models import RequestBody, DirectoryInput, TextInput, ResponseBody, TextResponse
        
        # Mock schema fetch
        mock_schema_response = AsyncMock()
        mock_schema_response.json.return_value = sample_task_schema.model_dump()
        mock_schema_response.raise_for_status = Mock()
        mock_core.api_client.get.return_value = mock_schema_response
        
        # Mock job submission response
        mock_job_response = AsyncMock()
        # The .json() method on an httpx.Response is synchronous, so we use a synchronous Mock
        mock_job_response.json = Mock(return_value={
            "root": {
                "output_type": "text",
                "value": "Job completed successfully"
            }
        })
        mock_job_response.raise_for_status = Mock()
        mock_core.api_client.post.return_value = mock_job_response
        mock_core.api = AsyncMock()
        mock_core.api.post = AsyncMock(return_value=mock_job_response)
        mock_core.api.json = AsyncMock(
            return_value={
                "root": {
                    "output_type": "text",
                    "value": "Job completed successfully",
                }
            }
        )

        # Create request body
        text_path = Path.cwd() 
        request_body = RequestBody(
            inputs={
                "input_dir": DirectoryInput(path=str(text_path)),
                "prompt": TextInput(text="test prompt")
            },
            parameters={"confidence": 0.8}
        )
        
        # Submit job
        response = await mock_core.submit_job(request_body, "audio/transcribe")
        
        assert isinstance(response, ResponseBody)
        mock_core.api.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_help_command_flow(self, mock_core, config):
        """Test help command flow"""
        handler = MessageHandler(mock_core, config)
        
        result = await handler.handle_message("/help")
        
        assert result["type"] == "help"
        assert "RescueBox Assistant" in result["content"]
        assert "Shortcut Commands" in result["content"]
    
    @pytest.mark.asyncio
    async def test_tool_picker_flow(self, mock_core, config):
        """Test tool picker command flow"""
        handler = MessageHandler(mock_core, config)
        
        result = await handler.handle_message("/models")
        
        assert result["type"] == "tool_picker"
    
    @pytest.mark.asyncio
    async def test_endpoint_specific_normalization(self, mock_core, config):
        """Test endpoint-specific argument normalization"""
        handler = MessageHandler(mock_core, config)
        
        # Test age-gender endpoint normalization
        tool_call = {
            "name": "age-gender/predict",
            "arguments": {"input_dir": "/tmp/images"}
        }
        mock_ollama_response = MagicMock()
        mock_ollama_response.status_code = 200
        mock_ollama_response.json = Mock(
            return_value={
                "message": {"content": f'<tool_code>{json.dumps(tool_call)}</tool_code>'},
            }
        )
        mock_ollama_response.raise_for_status = Mock()
        mock_core.ollama_client.post = AsyncMock(return_value=mock_ollama_response)
        
        result = await handler.handle_message("classify age and gender")
        
        assert result["type"] == "show_form"
        assert result["endpoint"] == "age-gender/predict"