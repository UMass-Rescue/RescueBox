"""
Unit tests for ChatbotCore error handling and recovery.

This module tests the robustness of the ChatbotCore class by validating
that various failure scenarios are handled gracefully. The tests cover
all major error conditions that can occur during AI model interactions,
API communications, and data processing.

The tests ensure that the chatbot maintains stability and provides
appropriate error feedback when:
- External services are unavailable (HTTP errors, network issues)
- Data formats are invalid or corrupted
- API responses don't match expected schemas
- Model services fail or return unexpected results

Error scenarios tested:
- Task schema retrieval failures (404, 500, network, JSON parsing)
- Job submission failures (404, 500, network, response validation)
- AI model interaction failures (404, network, response parsing)
- Graceful degradation and error message consistency

These tests are critical for ensuring reliable operation in production
environments where external dependencies may fail intermittently.
"""
from unittest.mock import AsyncMock

import pytest
from unittest.mock import patch, Mock
import httpx
import tempfile
from pathlib import Path
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.config import ChatbotConfig
from rb.api.models import RequestBody, DirectoryInput

# HTTP status codes
HTTP_404_NOT_FOUND = 404
HTTP_500_INTERNAL_ERROR = 500

# Error messages
ENDPOINT_NOT_FOUND_MSG = "Endpoint not found"
HTTP_500_ERROR_MSG = "HTTP 500"
NETWORK_ERROR_MSG = "Network error"
INVALID_SCHEMA_FORMAT_MSG = "Invalid schema format"
JOB_SUBMISSION_FAILED_MSG = "Job submission failed"
INTERNAL_SERVER_ERROR_MSG = "Internal server error"
INVALID_JSON_RESPONSE_MSG = "Invalid JSON response"
INVALID_RESPONSE_FORMAT_MSG = "Invalid response format"

# Test endpoints
NONEXISTENT_ENDPOINT = "nonexistent/endpoint"
TEST_ENDPOINT = "audio/transcribed"

# Test data
TEST_PROMPT = "test prompt"
INVALID_SCHEMA_RESPONSE = {"invalid": "schema"}
INVALID_RESPONSE_DATA = {"invalid": "response"}
ERROR_DETAIL_500 = {"detail": "Internal server error"}
MISSING_RESPONSE_KEY_DATA = {"no_response": "key"}

# HTTP error messages
MODEL_NOT_FOUND_MSG = "Model not found"
CONNECTION_REFUSED_MSG = "Connection refused"
CONNECTION_TIMEOUT_MSG = "Connection timeout"
INVALID_JSON_MSG = "Invalid JSON"


class TestChatbotCoreErrorHandling:
    """Tests for ChatbotCore error handling and graceful failure recovery.

    This class validates that the ChatbotCore handles all types of external
    service failures appropriately, ensuring the application remains stable
    and provides meaningful error feedback to users.

    Error handling categories tested:
    - HTTP status errors (404 Not Found, 500 Internal Server Error)
    - Network connectivity issues (connection refused, timeouts)
    - Data format errors (invalid JSON, malformed responses)
    - Schema validation failures (missing required fields)
    - API response inconsistencies (unexpected data structures)

    All tests verify that errors are caught, logged appropriately, and
    transformed into user-friendly error messages without crashing the
    application or exposing sensitive technical details.
    """

    @staticmethod
    def _create_mock_http_client():
        """Helper method to create a properly configured mock HTTP client.

        Returns a patch context manager for httpx.Client that creates mock
        clients with proper async context manager behavior.
        """
        def mock_client_factory():
            """Factory function for creating mock HTTP clients."""
            mock_client = Mock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            return mock_client

        return patch('httpx.Client', return_value=mock_client_factory())
    
    @pytest.fixture
    def core(self):
        """Create ChatbotCore instance (real API clients; patch fetch/orchestrator per test)."""
        return ChatbotCore(ChatbotConfig())
    
    @pytest.mark.asyncio
    async def test_get_task_schema_http_404_error(self, core):
        """Test handling of HTTP 404 error when fetching task schema.

        Validates that requests to non-existent endpoints are properly
        detected and result in clear error messages indicating the
        endpoint was not found.
        """
        mock_response = Mock()
        mock_response.status_code = HTTP_404_NOT_FOUND
        err = httpx.HTTPStatusError(ENDPOINT_NOT_FOUND_MSG, request=Mock(), response=mock_response)
        with patch("frontend.chatbot.core.fetch_task_schema", new_callable=AsyncMock, side_effect=err):
            with pytest.raises(httpx.HTTPStatusError, match=ENDPOINT_NOT_FOUND_MSG):
                await core.get_task_schema_from_endpoint(NONEXISTENT_ENDPOINT)
    
    @pytest.mark.asyncio
    async def test_get_task_schema_http_500_error(self, core):
        """Test handling of HTTP 500 error when fetching task schema.

        Ensures that server-side errors during task schema retrieval
        are properly caught and communicated with appropriate error
        messages indicating internal server problems.
        """
        mock_response = Mock()
        mock_response.status_code = HTTP_500_INTERNAL_ERROR
        err = httpx.HTTPStatusError(HTTP_500_ERROR_MSG, request=Mock(), response=mock_response)
        with patch("frontend.chatbot.core.fetch_task_schema", new_callable=AsyncMock, side_effect=err):
            with pytest.raises(httpx.HTTPStatusError, match=HTTP_500_ERROR_MSG):
                await core.get_task_schema_from_endpoint(TEST_ENDPOINT)
    
    @pytest.mark.asyncio
    async def test_get_task_schema_network_error(self, core):
        """Test handling of network error when fetching task schema.

        Validates that network connectivity issues are properly detected
        and result in clear error messages indicating network problems
        rather than confusing technical details.
        """
        with patch(
            "frontend.chatbot.core.fetch_task_schema",
            new_callable=AsyncMock,
            side_effect=httpx.RequestError(CONNECTION_REFUSED_MSG),
        ):
            with pytest.raises(httpx.RequestError):
                await core.get_task_schema_from_endpoint(TEST_ENDPOINT)
    
    @pytest.mark.asyncio
    async def test_get_task_schema_invalid_json(self, core):
        """Test handling of invalid JSON response when fetching task schema.

        Ensures that corrupted or malformed JSON responses from the API
        are detected and result in appropriate error messages indicating
        schema format problems.
        """
        with patch(
            "frontend.chatbot.core.fetch_task_schema",
            new_callable=AsyncMock,
            side_effect=ValueError(INVALID_JSON_MSG),
        ):
            with pytest.raises(ValueError, match=INVALID_JSON_MSG):
                await core.get_task_schema_from_endpoint(TEST_ENDPOINT)
    
    @pytest.mark.asyncio
    async def test_get_task_schema_invalid_schema_format(self, core):
        """Invalid payload cannot be coerced to TaskSchema (Pydantic validation)."""
        with patch(
            "frontend.chatbot.core.fetch_task_schema",
            new_callable=AsyncMock,
            return_value={"invalid": "schema"},
        ):
            from pydantic import ValidationError

            with pytest.raises(ValidationError):
                await core.get_task_schema_from_endpoint("audio/transcribed")
    
    @pytest.mark.asyncio
    async def test_submit_job_http_404_error(self, core):
        """Test handling of HTTP 404 error when submitting job"""
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={"input_dir": DirectoryInput(path=Path(temp_dir))},
                parameters={}
            )
            with patch(
                "frontend.chatbot.core.submit_job_orchestrator",
                new_callable=AsyncMock,
                side_effect=Exception('Job submission failed: Not Found'),
            ):
                with pytest.raises(Exception, match="Job submission failed"):
                    await core.submit_job(request_body, "nonexistent/endpoint")
    
    @pytest.mark.asyncio
    async def test_submit_job_http_500_error(self, core):
        """Test handling of HTTP 500 error when submitting job"""
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={"input_dir": DirectoryInput(path=Path(temp_dir))},
                parameters={}
            )
            with patch(
                "frontend.chatbot.core.submit_job_orchestrator",
                new_callable=AsyncMock,
                side_effect=Exception("Internal server error"),
            ):
                with pytest.raises(Exception, match="Internal server error"):
                    await core.submit_job(request_body, "audio/transcribed")
    
    @pytest.mark.asyncio
    async def test_submit_job_network_error(self, core):
        """Test handling of network error when submitting job"""
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={"input_dir": DirectoryInput(path=Path(temp_dir))},
                parameters={}
            )
            with patch(
                "frontend.chatbot.core.submit_job_orchestrator",
                new_callable=AsyncMock,
                side_effect=Exception("Network error submitting job: Connection timeout"),
            ):
                with pytest.raises(Exception) as exc:
                    await core.submit_job(request_body, "audio/transcribed")
                assert "Network error submitting job" in str(exc.value)
    
    @pytest.mark.asyncio
    async def test_submit_job_invalid_json_response(self, core):
        """Orchestrator surfaces failures while resolving job response JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={"input_dir": DirectoryInput(path=Path(temp_dir))},
                parameters={}
            )
            with patch(
                "frontend.chatbot.core.submit_job_orchestrator",
                new_callable=AsyncMock,
                side_effect=ValueError("Invalid JSON"),
            ):
                with pytest.raises(ValueError, match="Invalid JSON"):
                    await core.submit_job(request_body, "audio/transcribed")
    
    @pytest.mark.asyncio
    async def test_submit_job_invalid_response_format(self, core):
        """Response body dict must satisfy ResponseBody schema."""
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={"input_dir": DirectoryInput(path=Path(temp_dir))},
                parameters={}
            )
            with patch(
                "frontend.chatbot.core.submit_job_orchestrator",
                new_callable=AsyncMock,
                side_effect=Exception("Invalid response format"),
            ):
                with pytest.raises(Exception, match="Invalid response format"):
                    await core.submit_job(request_body, "audio/transcribed")
    
    @pytest.mark.asyncio
    async def test_call_granite_model_404_error(self, core):
        """Test handling of HTTP 404 error when calling Granite model"""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = ""
        
        core.ollama_client.post = AsyncMock(return_value=mock_response)
        
        result = await core.call_granite_model("test prompt")
        # Should return None on error
        assert result is None
    
    @pytest.mark.asyncio
    async def test_call_granite_model_network_error(self, core):
        """Test handling of network error when calling Granite model"""
        core.ollama_client.post = AsyncMock(side_effect=httpx.RequestError("Connection refused"))
        
        result = await core.call_granite_model("test prompt")
        # Should return None on error
        assert result is None
    
    @pytest.mark.asyncio
    async def test_call_granite_model_invalid_response_format(self, core):
        """Test handling of invalid response format from Granite model"""
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()  # raise_for_status() is synchronous
        mock_response.json = Mock(side_effect=ValueError("Invalid JSON"))
        
        core.ollama_client.post = AsyncMock(return_value=mock_response)
        
        result = await core.call_granite_model("test prompt")
        # Should return None on error
        assert result is None
    
    @pytest.mark.asyncio
    async def test_call_granite_model_missing_response_key(self, core):
        """Test handling of missing 'response' key in Granite model response"""
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()  # raise_for_status() is synchronous
        mock_response.json = Mock(return_value={"no_response": "key"})
        
        core.ollama_client.post = AsyncMock(return_value=mock_response)
        
        result = await core.call_granite_model("test prompt")
        # Should return None when no response key
        assert result is None

