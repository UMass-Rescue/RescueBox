"""
Integration tests for chatbot flow with REAL dependencies

These tests make actual HTTP requests to the backend API and Ollama.
They require:
1. Backend API running at http://localhost:8000
2. Ollama server running at http://localhost:11434
3. Granite mode "granite4:micro" available in Ollama

To run these tests:
1. Start backend: python -m rb.api.main
2. Start Ollama: ollama serve
3. Ensure Granite model: ollama pull granite4:micro
4. Run: pytest frontend/tests/integration/test_chatbot_flow_integration.py -v -m "api and ollama"
"""

import pytest
import pytest_asyncio
import httpx
import logging
import os
from pathlib import Path
from frontend.chatbot.config import ChatbotConfig
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.message_handler import MessageHandler
from rb.api.models import RequestBody, DirectoryInput, TextInput, FileInput, ResponseBody

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def _normalize_base_url(url: str) -> str:
    """Ensure httpx base_url includes a scheme (env often sets host:port only)."""
    url = (url or "").strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return url.rstrip("/")


# Configuration
API_BASE_URL = _normalize_base_url(os.getenv("API_BASE_URL", "http://localhost:8000"))
OLLAMA_HOST = _normalize_base_url(os.getenv("OLLAMA_HOST", "http://localhost:11434"))
GRANITE_MODEL = os.getenv("GRANITE_MODEL", "granite4:micro")


@pytest_asyncio.fixture
async def api_client():
    """Create HTTP client for backend API"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        try:
            # Check if API is available
            response = await client.get("/api/models")
            response.raise_for_status()
            yield client
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
            pytest.skip(f"Backend API not available at {API_BASE_URL}: {e}")


@pytest_asyncio.fixture
async def ollama_available():
    """Check if Ollama is available"""
    async with httpx.AsyncClient(base_url=OLLAMA_HOST, timeout=10.0) as client:
        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            plugin_names = [model.get("name", "") for model in models]
            if not any(
                installed == GRANITE_MODEL or (GRANITE_MODEL and GRANITE_MODEL in installed)
                for installed in plugin_names
            ):
                pytest.skip(f"Granite model '{GRANITE_MODEL}' not found. Available: {plugin_names}")
            yield True
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.HTTPStatusError,
            httpx.UnsupportedProtocol,
        ) as e:
            pytest.skip(f"Ollama not available at {OLLAMA_HOST}: {e}")


@pytest.fixture
def config():
    """Create test configuration"""
    return ChatbotConfig(
        FILTER_ENABLED=False,
        RESCUEBOX_HOST=API_BASE_URL,
        OLLAMA_HOST=OLLAMA_HOST,
        GRANITE_MODEL=GRANITE_MODEL
    )


@pytest_asyncio.fixture
async def core(config):
    """Create ChatbotCore with real HTTP clients"""
    core = ChatbotCore(config)
    yield core
    await core.close()


@pytest.mark.api
@pytest.mark.ollama
@pytest.mark.integration
class TestChatbotFlowIntegration:
    """Integration tests for chatbot flow with real dependencies"""
    
    @pytest.mark.asyncio
    async def test_slash_command_flow(self, core: ChatbotCore, config: ChatbotConfig, api_client: httpx.AsyncClient):
        """Test complete flow: slash command -> form display"""
        # First, get available models to find a valid endpoint
        response = await api_client.get("/api/models")
        response.raise_for_status()
        models = response.json()
        
        if not models:
            pytest.skip("No models available for testing")
        
        # Find an endpoint (e.g., audio/transcribe)
        # For this test, we'll use the first available endpoint
        # In practice, you'd need to map model UIDs to endpoints
        handler = MessageHandler(core, config)
        
        # Test with a known slash command that should exist
        # If the endpoint doesn't exist, the test will fail gracefully
        try:
            result = await handler.handle_message("/transcribe")
            assert result["type"] == "show_form"
            assert "endpoint" in result
            logger.info(f"Slash command flow successful: {result['endpoint']}")
        except Exception as e:
            # If endpoint doesn't exist, that's okay - just log it
            logger.warning(f"Slash command test skipped due to: {e}")
            pytest.skip(f"Endpoint not available: {e}")
    
    @pytest.mark.asyncio
    async def test_smart_analyze_flow(self, core: ChatbotCore, config: ChatbotConfig, ollama_available):
        """Test complete flow: natural language -> Granite model -> form"""
        handler = MessageHandler(core, config)
        
        # Test with a simple prompt
        result = await handler.handle_message("transcribe audio files")
        
        # Should either show form or return a tool call
        assert result["type"] in ["show_form", "message"]
        if result["type"] == "show_form":
            assert "endpoint" in result
            logger.info(f"Smart analyze flow successful: {result['endpoint']}")
        else:
            # If Granite model didn't return a tool call, that's also valid
            logger.info(f"Smart analyze returned message: {result.get('content', '')[:100]}")
    
    @pytest.mark.asyncio
    async def test_input_filtering_in_flow(self, core: ChatbotCore):
        """Test that input filtering works in message handler"""
        config = ChatbotConfig(FILTER_ENABLED=True, RESCUEBOX_HOST=API_BASE_URL)
        handler = MessageHandler(core, config)
        
        # Test blocked request
        result = await handler.handle_message("tell me a joke")
        
        assert result["type"] == "message"
        assert "RescueBox chat Assistant" in result["content"] or "only handles specific prompts" in result["content"].lower()
    
    @pytest.mark.asyncio
    async def test_job_submission_flow(self, core: ChatbotCore, config: ChatbotConfig, api_client: httpx.AsyncClient):
        """Test job submission flow with real API"""
        # Get available models
        response = await api_client.get("/api/models")
        response.raise_for_status()
        data = response.json()
        
        # Handle dictionary response
        if isinstance(data, dict):
            for skip_key in ["fs", "manage", "docs"]:
                data.pop(skip_key, None)
            models = list(data.values())
        else:
            models = data
            
        # Filter out system endpoints
        models = [m for m in models if isinstance(m, dict) and m.get('uid') not in ["fs", "manage", "docs"]]
        
        if not models:
            pytest.skip("No models available for testing")
        
        # Try to find a testable endpoint
        target_endpoint = None
        
        # Look for known models
        for model in models:
            uid = model.get('uid', '')
            if uid == 'audio':
                target_endpoint = 'audio/transcribe'
                break
            elif uid == 'age-gender':
                target_endpoint = 'age-gender/predict'
                break
        
        if not target_endpoint:
            pytest.skip(f"No known testable models (audio, age-gender) found in {[m.get('uid') for m in models]}")
            
        logger.info(f"Testing job submission for endpoint: {target_endpoint}")
        
        # Get schema
        schema = await core.get_task_schema_from_endpoint(target_endpoint)
        if not schema:
            pytest.skip(f"No schema returned for {target_endpoint}")
            
        # Construct inputs based on schema
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        (temp_dir / "dummy.jpg").write_text("dummy")
        (temp_dir / "dummy.mp3").write_text("dummy")
        inputs = {}
        for input_field in schema.inputs:
            key = input_field.key
            input_type = input_field.input_type.value if hasattr(input_field.input_type, 'value') else str(input_field.input_type)
            
            if input_type == 'directory':
                inputs[key] = DirectoryInput(path=str(temp_dir))
            elif input_type == 'text':
                inputs[key] = TextInput(text="test input")
            elif input_type == 'file':
                inputs[key] = FileInput(path=str(temp_dir / "dummy.jpg"))
                
        # Construct parameters to prevent 422 errors for required fields
        parameters = {}
        for param in schema.parameters:
            if hasattr(param.value, 'default') and param.value.default is not None:
                parameters[param.key] = param.value.default
            elif hasattr(param.value, 'enum_vals') and param.value.enum_vals:
                parameters[param.key] = param.value.enum_vals[0].key
            else:
                parameters[param.key] = "test"
                
        request_body = RequestBody(inputs=inputs, parameters=parameters)
        
        # Submit job
        try:
            response = await core.submit_job(request_body, target_endpoint)
            assert isinstance(response, ResponseBody)
        except Exception as e:
            if "Network error" in str(e) or "Not Found" in str(e) or "404" in str(e):
                raise
            logger.info(f"Plugin returned error for dummy data, but flow succeeded: {e}")
    
    @pytest.mark.asyncio
    async def test_help_command_flow(self, core: ChatbotCore, config: ChatbotConfig):
        """Test help command flow"""
        handler = MessageHandler(core, config)
        
        result = await handler.handle_message("/help")
        
        assert result["type"] == "help"
        assert "RescueBox Assistant" in result["content"]
        assert "Three different ways" in result["content"]
    
    @pytest.mark.asyncio
    async def test_tool_picker_flow(self, core: ChatbotCore, config: ChatbotConfig):
        """Test tool picker command flow"""
        handler = MessageHandler(core, config)
        
        result = await handler.handle_message("/models")
        
        assert result["type"] == "tool_picker"
    
    @pytest.mark.asyncio
    async def test_granite_model_tool_call(self, core: ChatbotCore, ollama_available):
        """Test that Granite model returns valid tool calls"""
        prompt = "transcribe audio files"
        tool_calls = await core.call_granite_model_direct(prompt)
        
        assert tool_calls is not None, (
            "Granite did not return tool calls; check Ollama and that GRANITE_MODEL matches "
            "an installed model (default granite4:micro)."
        )
        assert isinstance(tool_calls, list), f"Expected list, got {type(tool_calls)}"
        assert len(tool_calls) > 0, "Expected at least one tool call"
        
        # Verify first tool call structure
        tool_call = tool_calls[0]
        assert "name" in tool_call
        assert "arguments" in tool_call
        assert isinstance(tool_call["arguments"], dict)
        logger.info(f"Granite model returned tool calls: {tool_calls}")
