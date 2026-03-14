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
from unittest.mock import AsyncMock, patch, Mock, MagicMock
import httpx
import tempfile
from pathlib import Path
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.config import ChatbotConfig
from rb.api.models import TaskSchema, InputSchema, ParameterSchema, InputType, RequestBody, DirectoryInput

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
        """Create ChatbotCore instance"""
        config = ChatbotConfig()
        core = ChatbotCore(config)
        core.api_client = AsyncMock()
        return ChatbotCore(config)
    
    @pytest.mark.asyncio
    async def test_get_task_schema_http_404_error(self, core):
        """Test handling of HTTP 404 error when fetching task schema.

        Validates that requests to non-existent endpoints are properly
        detected and result in clear error messages indicating the
        endpoint was not found.
        """
        mock_response = AsyncMock()
        mock_response.status_code = HTTP_404_NOT_FOUND
        mock_response.json = Mock(return_value={})  # json() is synchronous
        mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
            "Not Found", request=AsyncMock(), response=mock_response
        ))

        core.api_client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(Exception, match=ENDPOINT_NOT_FOUND_MSG):
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
        mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
            "Internal Server Error", request=Mock(), response=mock_response
        ))

        with self._create_mock_http_client() as mock_client_patch:
            mock_client_patch.return_value.get = Mock(return_value=mock_response)

            with pytest.raises(Exception, match=HTTP_500_ERROR_MSG):
                await core.get_task_schema_from_endpoint(TEST_ENDPOINT)
    
    @pytest.mark.asyncio
    async def test_get_task_schema_network_error(self, core):
        """Test handling of network error when fetching task schema.

        Validates that network connectivity issues are properly detected
        and result in clear error messages indicating network problems
        rather than confusing technical details.
        """
        with self._create_mock_http_client() as mock_client_patch:
            mock_client_patch.return_value.get = Mock(side_effect=httpx.RequestError(CONNECTION_REFUSED_MSG))

            with pytest.raises(Exception, match=NETWORK_ERROR_MSG):
                await core.get_task_schema_from_endpoint(TEST_ENDPOINT)
    
    @pytest.mark.asyncio
    async def test_get_task_schema_invalid_json(self, core):
        """Test handling of invalid JSON response when fetching task schema.

        Ensures that corrupted or malformed JSON responses from the API
        are detected and result in appropriate error messages indicating
        schema format problems.
        """
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(side_effect=ValueError(INVALID_JSON_MSG))

        with self._create_mock_http_client() as mock_client_patch:
            mock_client_patch.return_value.get = Mock(return_value=mock_response)

            with pytest.raises(Exception, match=INVALID_SCHEMA_FORMAT_MSG):
                await core.get_task_schema_from_endpoint(TEST_ENDPOINT)
    
    @pytest.mark.asyncio
    async def test_get_task_schema_invalid_schema_format(self, core):
        """Test handling of invalid schema format (missing required fields)"""
        import httpx

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"invalid": "schema"}

        with patch('httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client.get = Mock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            with pytest.raises(Exception, match="Invalid schema format"):
                await core.get_task_schema_from_endpoint("audio/transcribed")
    
    @pytest.mark.asyncio
    async def test_submit_job_http_404_error(self, core):
        """Test handling of HTTP 404 error when submitting job"""
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={"input_dir": DirectoryInput(path=Path(temp_dir))},
                parameters={}
            )
            
            mock_request = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.request = mock_request
            mock_response.json = Mock(return_value={})  # Mock json() method
            
            # Create HTTPStatusError that will be raised by raise_for_status
            http_error = httpx.HTTPStatusError(
                "Not Found", request=mock_request, response=mock_response
            )
            mock_response.raise_for_status = Mock(side_effect=http_error)
            
            # Mock the api_client.post method properly
            with patch.object(core.api_client, 'post', new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response
                
                with pytest.raises(Exception) as exc_info:
                    await core.submit_job(request_body, "nonexistent/endpoint")
                # Check that it raises an exception with proper error message
                error_str = str(exc_info.value)
                assert "Job submission failed" in error_str or "404" in error_str
    
    @pytest.mark.asyncio
    async def test_submit_job_http_500_error(self, core):
        """Test handling of HTTP 500 error when submitting job"""
        import httpx
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={"input_dir": DirectoryInput(path=Path(temp_dir))},
                parameters={}
            )

            mock_response = Mock()
            mock_response.status_code = 500
            error_detail = {"detail": "Internal server error"}
            mock_response.json = Mock(return_value=error_detail)
            mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
                "Internal Server Error", request=Mock(), response=mock_response
            ))

            with patch('httpx.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.__enter__ = Mock(return_value=mock_client)
                mock_client.__exit__ = Mock(return_value=None)
                mock_client.post = Mock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                with pytest.raises(Exception, match="Internal server error"):
                    await core.submit_job(request_body, "audio/transcribed")
    
    @pytest.mark.asyncio
    async def test_submit_job_network_error(self, core):
        """Test handling of network error when submitting job"""
        import httpx
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={"input_dir": DirectoryInput(path=Path(temp_dir))},
                parameters={}
            )

            with patch('httpx.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.__enter__ = Mock(return_value=mock_client)
                mock_client.__exit__ = Mock(return_value=None)
                mock_client.post = Mock(side_effect=httpx.RequestError("Connection timeout"))
                mock_client_class.return_value = mock_client

                with pytest.raises(Exception, match="Network error"):
                    await core.submit_job(request_body, "audio/transcribed")
    
    @pytest.mark.asyncio
    async def test_submit_job_invalid_json_response(self, core):
        """Test handling of invalid JSON response when submitting job"""
        import httpx
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={"input_dir": DirectoryInput(path=Path(temp_dir))},
                parameters={}
            )

            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(side_effect=ValueError("Invalid JSON"))

            with patch('httpx.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.__enter__ = Mock(return_value=mock_client)
                mock_client.__exit__ = Mock(return_value=None)
                mock_client.post = Mock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                with pytest.raises(Exception, match="Invalid JSON response"):
                    await core.submit_job(request_body, "audio/transcribed")
    
    @pytest.mark.asyncio
    async def test_submit_job_invalid_response_format(self, core):
        """Test handling of invalid response format when submitting job"""
        import httpx
        with tempfile.TemporaryDirectory() as temp_dir:
            request_body = RequestBody(
                inputs={"input_dir": DirectoryInput(path=Path(temp_dir))},
                parameters={}
            )

            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.json = Mock(return_value={"invalid": "response"})

            with patch('httpx.Client') as mock_client_class:
                mock_client = Mock()
                mock_client.__enter__ = Mock(return_value=mock_client)
                mock_client.__exit__ = Mock(return_value=None)
                mock_client.post = Mock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                with pytest.raises(Exception, match="Invalid response format"):
                    await core.submit_job(request_body, "audio/transcribed")
    
    @pytest.mark.asyncio
    async def test_call_granite_model_404_error(self, core):
        """Test handling of HTTP 404 error when calling Granite model"""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
            "Model not found", request=AsyncMock(), response=mock_response
        ))
        
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

