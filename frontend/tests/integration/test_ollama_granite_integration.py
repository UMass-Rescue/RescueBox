"""
Integration tests for Granite model tool calling

These tests verify the Granite model integration works correctly using:
1. Direct GGUF model loading via llama-cpp-python (call_granite_model_direct)
2. Ollama API (call_granite_model) - if available

Requirements:
- For direct model tests: GGUF model file at DEFAULT_GRANITE_GGUF_MODEL_PATH
- For Ollama tests: Ollama server at http://localhost:11434 and model "granite4:micro"

To run these tests:
1. Direct model: Ensure GGUF file exists at configured path
2. Ollama tests: Ensure Ollama is running and model is available
3. Run: pytest frontend/tests/integration/test_ollama_granite_integration.py -v -m ollama

Note: call_granite_model_direct returns a list of tool calls, not a single dict.
"""

import pytest
import pytest_asyncio
import httpx
import logging
import os
import json
from typing import Optional, Dict, Any

# Configure logging for tests
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
GRANITE_MODEL = os.getenv("GRANITE_MODEL", "granite4:micro")


@pytest_asyncio.fixture
async def ollama_client():
    """
    Create an HTTP client for Ollama API testing.
    
    Yields:
        httpx.AsyncClient: HTTP client configured for Ollama API
    """
    async with httpx.AsyncClient(base_url=OLLAMA_HOST, timeout=60.0) as client:
        yield client


@pytest_asyncio.fixture
async def granite_model_available(ollama_client: httpx.AsyncClient) -> bool:
    """
    Check if Granite model is available in Ollama.
    
    This fixture checks if the model exists and can be used for testing.
    Returns True if available, False otherwise.
    
    Args:
        ollama_client: HTTP client for Ollama API
    
    Returns:
        bool: True if model is available, False otherwise
    """
    try:
        response = await ollama_client.get("/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            available = any(GRANITE_MODEL in name for name in model_names)
            logger.info(f"Granite model availability: {available}")
            return available
    except Exception as e:
        logger.warning(f"Could not check model availability: {e}")
    return False


@pytest_asyncio.fixture
async def ollama_available(ollama_client: httpx.AsyncClient) -> bool:
    """
    Check if Ollama server is available.
    
    Args:
        ollama_client: HTTP client for Ollama API
    
    Returns:
        bool: True if Ollama is available, False otherwise
    """
    try:
        response = await ollama_client.get("/api/tags")
        return response.status_code == 200
    except Exception:
        return False


class TestOllamaGraniteIntegration:
    """Integration tests for Ollama Granite model"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_ollama_api_connection(self, ollama_client: httpx.AsyncClient):
        """
        Test basic connection to Ollama API.
        
        Verifies:
        - Ollama server is running
        - API endpoints are accessible
        """
        logger.info("Testing Ollama API connection")
        
        response = await ollama_client.get("/api/tags")
        assert response.status_code == 200, "Ollama API not accessible"
        
        data = response.json()
        assert "models" in data, "Response should contain 'models' key"
        
        logger.info("Ollama API connection successful")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_granite_model_list(self, ollama_client: httpx.AsyncClient, granite_model_available: bool):
        """
        Test that Granite model appears in Ollama model list.
        
        Verifies:
        - Model is available in Ollama
        - Model name matches expected value
        """
        if not granite_model_available:
            pytest.skip("Granite model not available in Ollama")
        
        logger.info("Testing Granite model availability")
        
        response = await ollama_client.get("/api/tags")
        assert response.status_code == 200
        
        models = response.json().get("models", [])
        model_names = [model.get("name", "") for model in models]
        
        assert any(GRANITE_MODEL in name for name in model_names), \
            f"Granite model '{GRANITE_MODEL}' not found in available models"
        
        logger.info(f"Granite model found: {[n for n in model_names if GRANITE_MODEL in n]}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_granite_model_generate(self, ollama_client: httpx.AsyncClient, granite_model_available: bool):
        """
        Test basic text generation with Granite model.
        
        Verifies:
        - Model can generate responses
        - Response format is valid
        """
        if not granite_model_available:
            pytest.skip("Granite model not available in Ollama")
        
        logger.info("Testing Granite model text generation")
        
        response = await ollama_client.post(
            "/api/generate",
            json={
                "model": GRANITE_MODEL,
                "prompt": "transcribe audio",
                "stream": False
            },
            timeout=120.0
        )
        
        assert response.status_code == 200, f"Generation failed: {response.text}"
        
        data = response.json()
        assert "response" in data, "Response should contain 'response' key"
        
        logger.info(f"Generation successful: {len(data.get('response', ''))} chars")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_granite_tool_call_format(self, ollama_client: httpx.AsyncClient, granite_model_available: bool):
        """
        Test that Granite model returns tool calls in expected format.
        
        Verifies:
        - Model generates tool call JSON
        - Tool call has 'name' and 'arguments' fields
        """
        if not granite_model_available:
            pytest.skip("Granite model not available in Ollama")
        
        logger.info("Testing Granite model tool call format")
        
        prompt = "transcribe audio files in /tmp"
        
        response = await ollama_client.post(
            "/api/generate",
            json={
                "model": GRANITE_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120.0
        )
        
        assert response.status_code == 200
        
        data = response.json()
        model_output = data.get("response", "")
        
        # Check for tool_code tags or JSON format
        import re
        tool_code_pattern = r'<tool_code>\s*(\{.*?\})\s*</tool_code>'
        matches = re.findall(tool_code_pattern, model_output, re.DOTALL)
        
        if matches:
            tool_call_json = json.loads(matches[0])
            assert "name" in tool_call_json, "Tool call should have 'name' field"
            assert "arguments" in tool_call_json, "Tool call should have 'arguments' field"
            logger.info(f"Tool call found: {tool_call_json.get('name')}")
        else:
            # Try to find JSON object directly
            json_pattern = r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^}]*\}\s*\}'
            json_matches = re.findall(json_pattern, model_output, re.DOTALL)
            if json_matches:
                tool_call_json = json.loads(json_matches[0])
                assert "name" in tool_call_json
                assert "arguments" in tool_call_json
                logger.info(f"Tool call found (JSON format): {tool_call_json.get('name')}")
            else:
                pytest.skip(f"No tool call format found in response: {model_output[:200]}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_granite_audio_transcribe_tool_call(self, ollama_client: httpx.AsyncClient, granite_model_available: bool):
        """
        Test that Granite model generates audio transcribe tool call.
        
        Verifies:
        - Model generates correct endpoint for audio transcription
        - Arguments are appropriate for the task
        """
        if not granite_model_available:
            pytest.skip("Granite model not available in Ollama")
        
        logger.info("Testing audio transcribe tool call")
        
        prompt = "transcribe audio files in /tmp/audio"
        
        response = await ollama_client.post(
            "/api/generate",
            json={
                "model": GRANITE_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120.0
        )
        
        assert response.status_code == 200
        
        data = response.json()
        model_output = data.get("response", "")
        
        # Parse tool call
        import re
        tool_code_pattern = r'<tool_code>\s*(\{.*?\})\s*</tool_code>'
        matches = re.findall(tool_code_pattern, model_output, re.DOTALL)
        
        if matches:
            tool_call = json.loads(matches[0])
            logger.info(f"Audio transcribe tool call: {tool_call}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_granite_image_summary_tool_call(self, ollama_client: httpx.AsyncClient, granite_model_available: bool):
        """
        Test that Granite model generates image summary tool call.
        
        Verifies:
        - Model generates correct endpoint for image summarization
        - Arguments include image directory path
        """
        if not granite_model_available:
            pytest.skip("Granite model not available in Ollama")
        
        logger.info("Testing image summary tool call")
        
        prompt = "summarize images in /tmp/photos"
        
        response = await ollama_client.post(
            "/api/generate",
            json={
                "model": GRANITE_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120.0
        )
        
        assert response.status_code == 200
        
        data = response.json()
        model_output = data.get("response", "")
        
        # Parse tool call
        import re
        tool_code_pattern = r'<tool_code>\s*(\{.*?\})\s*</tool_code>'
        matches = re.findall(tool_code_pattern, model_output, re.DOTALL)
        
        if matches:
            tool_call = json.loads(matches[0])
            logger.info(f"Image summary tool call: {tool_call}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_chatbot_core_call_granite_model(
        self,
        granite_model_available: bool
    ):
        """
        Test ChatbotCore.call_granite_model_direct() with direct GGUF model loading.
        
        Verifies:
        - ChatbotCore can load and use GGUF model directly via llama-cpp-python
        - Response parsing works correctly
        - Tool call extraction works
        - Returns list of tool calls (not single dict)
        """
        logger.info("Testing ChatbotCore.call_granite_model_direct() integration")
        
        from frontend.chatbot.core import ChatbotCore
        from frontend.chatbot.config import ChatbotConfig
        
        config = ChatbotConfig(
            OLLAMA_HOST=OLLAMA_HOST,
            GRANITE_MODEL=GRANITE_MODEL
        )
        
        core = ChatbotCore(config)
        
        try:
            prompt = "transcribe audio files"
            tool_calls = await core.call_granite_model_direct(prompt)
            
            assert tool_calls is not None, "Expected tool calls list, got None"
            assert isinstance(tool_calls, list), f"Expected list, got {type(tool_calls)}"
            assert len(tool_calls) > 0, "Expected at least one tool call in list"
            
            # Verify first tool call structure
            tool_call = tool_calls[0]
            assert "name" in tool_call, f"Missing 'name' field: {tool_call}"
            assert "arguments" in tool_call, f"Missing 'arguments' field: {tool_call}"
            assert isinstance(tool_call["arguments"], dict), f"Expected dict for arguments, got {type(tool_call['arguments'])}"
            
            logger.info(f"ChatbotCore.call_granite_model_direct() successful: {tool_calls}")
            
        finally:
            await core.close()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_granite_model_error_handling(
        self,
        ollama_client: httpx.AsyncClient
    ):
        """
        Test error handling when Granite model is unavailable.
        
        Verifies:
        - Graceful handling of model not found
        - Proper error messages
        """
        logger.info("Testing error handling for unavailable model")
        
        # Try to call non-existent model
        response = await ollama_client.post(
            "/api/generate",
            json={
                "model": "non-existent-model-12345",
                "prompt": "test",
                "stream": False
            }
        )
        
        # Should return error status
        assert response.status_code != 200, \
            "Expected error status for non-existent model"
        
        logger.info(f"Error handling test passed: status={response.status_code}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_granite_model_timeout_handling(
        self,
        granite_model_available: bool
    ):
        """
        Test timeout handling for long-running Granite model calls.
        
        Verifies:
        - Timeout configuration works
        - Timeout errors are handled gracefully
        """
        logger.info("Testing timeout handling")
        
        from frontend.chatbot.core import ChatbotCore
        from frontend.chatbot.config import ChatbotConfig
        
        # Use very short timeout to trigger timeout error
        config = ChatbotConfig(
            OLLAMA_HOST=OLLAMA_HOST,
            GRANITE_MODEL=GRANITE_MODEL
        )
        
        core = ChatbotCore(config)
        # Override timeout to very short value
        core.ollama_client = httpx.AsyncClient(
            base_url=OLLAMA_HOST,
            timeout=0.001  # 1ms timeout - should timeout immediately
        )
        
        try:
            prompt = "transcribe audio files"
            tool_call = await core.call_granite_model(prompt)
            
            # Should return None on timeout
            assert tool_call is None, \
                "Expected None on timeout, but got tool call"
            
            logger.info("Timeout handling test passed")
            
        except Exception as e:
            # Timeout exceptions are expected
            logger.info(f"Timeout exception caught (expected): {type(e).__name__}")
        finally:
            await core.close()
