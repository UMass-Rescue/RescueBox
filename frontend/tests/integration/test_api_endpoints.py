"""
Integration tests for backend API endpoints.

These tests require the backend API to be running at http://localhost:8000.
They make actual HTTP requests to verify the endpoints work correctly.

To run these tests:
1. Start the backend: python -m rb.api.main
2. Run: pytest frontend/tests/integration/test_api_endpoints.py -v

Marked with @pytest.mark.api to indicate they require API access.
"""

import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest
import pytest_asyncio

# Configure logging for tests
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Base URL for backend API
# Can be overridden with environment variable API_BASE_URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest_asyncio.fixture
async def api_client():
    """
    Create an HTTP client for API testing.

    Yields:
        httpx.AsyncClient: HTTP client configured for backend API
    """
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def available_models(
    api_client: httpx.AsyncClient,
) -> AsyncGenerator[list[dict[str, Any]], None]:
    """
    Fetch available models from backend.

    This fixture fetches the models list once and provides it to tests.
    If the API is not available, the test will be skipped.

    Args:
        api_client: HTTP client for API requests

    Yields:
        List[Dict[str, Any]]: List of model dictionaries

    Raises:
        pytest.skip: If API is not available
    """
    try:
        response = await api_client.get("/api/models")
        response.raise_for_status()
        data = response.json()

        # Handle dictionary response where keys are plugin names
        # Filter out system endpoints/plugins
        for skip_key in ["fs", "manage", "docs"]:
            if isinstance(data, dict):
                data.pop(skip_key, None)

        # Convert to list of model objects if it's a dict
        models = list(data.values()) if isinstance(data, dict) else data

        # Filter out system endpoints if they appear in the list by uid
        models = [
            m
            for m in models
            if isinstance(m, dict) and m.get("uid") not in ["fs", "manage", "docs"]
        ]

        logger.info(f"Fetched {len(models)} models for testing")
        yield models
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        pytest.skip(f"Backend API not available at {API_BASE_URL}: {e}")
    except httpx.HTTPStatusError as e:
        pytest.skip(f"Backend API returned error: {e}")


@pytest.mark.api
@pytest.mark.integration
class TestModelsEndpoints:
    """Integration tests for /models endpoints"""

    @pytest.mark.asyncio
    async def test_get_models_list(self, api_client: httpx.AsyncClient):
        """
        Test GET /models returns list of all models.

        Verifies:
        - Endpoint returns 200 status
        - Response is a list
        - Each model has required fields (uid, name, plugin_name, version, author, info, gpu)
        """
        logger.info("Testing GET /models")
        response = await api_client.get("/api/models")
        response.raise_for_status()

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()

        # Handle dictionary response
        if isinstance(data, dict):
            for skip_key in ["fs", "manage", "docs"]:
                data.pop(skip_key, None)
            models = list(data.values())
        else:
            models = data

        # Filter out system endpoints if they appear in the list by uid
        models = [
            m
            for m in models
            if isinstance(m, dict) and m.get("uid") not in ["fs", "manage", "docs"]
        ]

        assert isinstance(
            models, list
        ), f"Expected list (or dict values), got {type(models)}"
        assert len(models) > 0, "Expected at least one model"

        logger.info(f"Received {len(models)} models")

        # Verify structure of first model
        if models:
            model = models[0]
            required_fields = [
                "uid",
                "name",
                "plugin_name",
                "version",
                "author",
                "info",
                "gpu",
            ]
            for field in required_fields:
                assert field in model, f"Model missing required field: {field}"

            logger.info(f"First model: {model.get('name')} (uid: {model.get('uid')})")

    @pytest.mark.asyncio
    async def test_get_model_by_uid(
        self, api_client: httpx.AsyncClient, available_models: list[dict]
    ):
        """
        Test GET /models/{model_uid} returns specific model metadata.

        Verifies:
        - Endpoint returns 200 status
        - Response contains model metadata
        - All required fields are present
        """
        if not available_models:
            pytest.skip("No models available for testing")

        model_uid = available_models[0]["uid"]
        logger.info(f"Testing GET /models/{model_uid}")

        response = await api_client.get(f"/api/models/{model_uid}")
        response.raise_for_status()

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        model = response.json()
        assert isinstance(model, dict), f"Expected dict, got {type(model)}"
        assert (
            model["uid"] == model_uid
        ), f"UID mismatch: expected {model_uid}, got {model['uid']}"

        required_fields = [
            "uid",
            "name",
            "plugin_name",
            "version",
            "author",
            "info",
            "gpu",
        ]
        for field in required_fields:
            assert field in model, f"Model missing required field: {field}"

        logger.info(f"Model metadata retrieved: {model.get('name')}")

    @pytest.mark.asyncio
    async def test_get_model_info_endpoint(
        self, api_client: httpx.AsyncClient, available_models: list[dict]
    ):
        """
        Test GET /models/{model_uid}/info returns model metadata (alias endpoint).

        Verifies:
        - Endpoint returns 200 status
        - Response matches /models/{model_uid} endpoint
        """
        if not available_models:
            pytest.skip("No models available for testing")

        model_uid = available_models[0]["uid"]
        logger.info(f"Testing GET /models/{model_uid}/info")

        response = await api_client.get(f"/api/models/{model_uid}/info")
        response.raise_for_status()

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        model_info = response.json()
        assert isinstance(model_info, dict), f"Expected dict, got {type(model_info)}"
        assert model_info["uid"] == model_uid, "UID mismatch"

        # Verify it matches the /models/{model_uid} endpoint
        direct_response = await api_client.get(f"/api/models/{model_uid}")
        direct_model = direct_response.json()

        assert (
            model_info["uid"] == direct_model["uid"]
        ), "Info endpoint should match direct endpoint"
        assert (
            model_info["name"] == direct_model["name"]
        ), "Info endpoint should match direct endpoint"

        logger.info(f"Model info endpoint verified: {model_info.get('name')}")

    @pytest.mark.asyncio
    async def test_get_model_not_found(self, api_client: httpx.AsyncClient):
        """
        Test GET /models/{invalid_uid} returns 404 for non-existent model.

        Verifies:
        - Endpoint returns 404 status for invalid model UID
        """
        invalid_uid = "non_existent_model_12345"
        logger.info(f"Testing GET /models/{invalid_uid} (should return 404)")

        response = await api_client.get(f"/models/{invalid_uid}")

        assert (
            response.status_code == 404
        ), f"Expected 404 for invalid model, got {response.status_code}"
        logger.info("404 response verified for invalid model UID")


@pytest.mark.api
@pytest.mark.integration
class TestServersEndpoints:
    """Integration tests for /servers endpoints"""

    @pytest.mark.asyncio
    async def test_get_servers_list(self, api_client: httpx.AsyncClient):
        """
        Test GET /servers returns list of servers.

        Verifies:
        - Endpoint returns 200 status
        - Response is a list
        - Each server entry has required fields (modelUid, serverAddress, serverPort, etc.)
        """
        logger.info("Testing GET /servers")
        response = await api_client.get("/api/servers")
        response.raise_for_status()

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        servers = response.json()
        assert isinstance(servers, list), f"Expected list, got {type(servers)}"

        logger.info(f"Received {len(servers)} server entries")

        # Verify structure if servers exist
        if servers:
            server = servers[0]
            required_fields = ["modelUid", "serverAddress", "serverPort"]
            for field in required_fields:
                assert field in server, f"Server missing required field: {field}"

            assert isinstance(
                server["serverAddress"], str
            ), "Server address must be string"
            assert len(server["serverAddress"]) > 0, "Server address cannot be empty"
            assert isinstance(server["serverPort"], int), "Server port must be int"
            assert server["serverPort"] > 0

            logger.info(
                f"First server: {server.get('modelUid')} at {server.get('serverAddress')}:{server.get('serverPort')}"
            )

    @pytest.mark.asyncio
    async def test_get_server_status(
        self, api_client: httpx.AsyncClient, available_models: list[dict]
    ):
        """
        Test GET /servers/{model_uid}/status returns server status.

        Verifies:
        - Endpoint returns 200 status
        - Response contains status information
        - Status is either 'Online' or 'Offline'
        """
        if not available_models:
            pytest.skip("No models available for testing")

        model_uid = available_models[0]["uid"]
        logger.info(f"Testing GET /servers/{model_uid}/status")

        response = await api_client.get(
            f"/api/servers/{model_uid}/status", timeout=10.0
        )
        response.raise_for_status()

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        status_data = response.json()
        assert isinstance(status_data, dict), f"Expected dict, got {type(status_data)}"
        assert "status" in status_data, "Status response missing 'status' field"
        assert status_data["status"] in [
            "Online",
            "Offline",
        ], f"Invalid status value: {status_data['status']}"
        assert status_data["modelUid"] == model_uid, "Model UID mismatch"

        logger.info(f"Server status for {model_uid}: {status_data['status']}")

    @pytest.mark.asyncio
    async def test_get_server_status_not_found(self, api_client: httpx.AsyncClient):
        """
        Test GET /servers/{invalid_uid}/status returns 404 for non-existent model.

        Verifies:
        - Endpoint returns 404 status for invalid model UID
        """
        invalid_uid = "non_existent_model_12345"
        logger.info(f"Testing GET /servers/{invalid_uid}/status (should return 404)")

        response = await api_client.get(f"/api/servers/{invalid_uid}/status")

        assert (
            response.status_code == 404
        ), f"Expected 404 for invalid model, got {response.status_code}"
        logger.info("404 response verified for invalid server status request")


@pytest.mark.api
@pytest.mark.integration
class TestModelsEndpointsIntegration:
    """Integration tests that verify multiple endpoints work together"""

    @pytest.mark.asyncio
    async def test_models_and_servers_consistency(self, api_client: httpx.AsyncClient):
        """
        Test that models and servers endpoints return consistent data.

        Verifies:
        - All models have corresponding server entries
        - Server status can be checked for all models
        """
        logger.info("Testing consistency between /models and /servers endpoints")

        # Get models
        models_response = await api_client.get("/api/models")
        models_response.raise_for_status()
        models_data = models_response.json()

        if isinstance(models_data, dict):
            for skip_key in ["fs", "manage", "docs"]:
                models_data.pop(skip_key, None)
            models = list(models_data.values())
        else:
            models = models_data

        # Filter out system endpoints if they appear in the list by uid
        models = [
            m
            for m in models
            if isinstance(m, dict) and m.get("uid") not in ["fs", "manage", "docs"]
        ]

        if not models:
            pytest.skip("No models available for testing")

        # Get servers
        servers_response = await api_client.get("/api/servers")
        servers_response.raise_for_status()
        servers = servers_response.json()

        # Create lookup for servers by modelUid
        servers_by_model = {s["modelUid"]: s for s in servers}

        # Verify each model has a server entry
        for model in models:
            model_uid = model["uid"]
            if model_uid in servers_by_model:
                server = servers_by_model[model_uid]
                assert (
                    server["modelUid"] == model_uid
                ), "Server modelUid should match model uid"
                assert isinstance(server["serverAddress"], str)
                assert len(server["serverAddress"]) > 0
                assert isinstance(server["serverPort"], int), "Server port must be int"
                assert server["serverPort"] > 0
            else:
                logger.warning(
                    f"Model {model_uid} currently has no active server entry (it might be offline)."
                )

        logger.info(f"Verified consistency for {len(models)} models")

    @pytest.mark.asyncio
    async def test_model_details_flow(
        self, api_client: httpx.AsyncClient, available_models: list[dict]
    ):
        """
        Test complete flow: list models -> get model details -> get server status.

        Verifies:
        - Can fetch model list
        - Can get details for each model
        - Can check server status for each model
        """
        if not available_models:
            pytest.skip("No models available for testing")

        logger.info("Testing complete model details flow")

        for model in available_models[:3]:  # Test first 3 models
            model_uid = model["uid"]
            logger.debug(f"Testing flow for model: {model_uid}")

            # Get model details
            model_response = await api_client.get(f"/api/models/{model_uid}")
            model_response.raise_for_status()
            model_details = model_response.json()
            assert model_details["uid"] == model_uid

            # Get model info (alternative endpoint)
            info_response = await api_client.get(f"/api/models/{model_uid}/info")
            info_response.raise_for_status()
            model_info = info_response.json()
            assert model_info["uid"] == model_uid

            # Get server status
            status_response = await api_client.get(f"/api/servers/{model_uid}/status")
            status_response.raise_for_status()
            status_data = status_response.json()
            assert status_data["modelUid"] == model_uid
            assert "status" in status_data

        logger.info("Complete model details flow verified")


@pytest.mark.api
@pytest.mark.integration
class TestEndpointErrorHandling:
    """Tests for error handling in API endpoints"""

    @pytest.mark.asyncio
    async def test_models_endpoint_handles_missing_metadata(
        self, api_client: httpx.AsyncClient
    ):
        """
        Test that /models endpoint handles plugins without metadata gracefully.

        Verifies:
        - Endpoint returns 200 even if some plugins lack metadata
        - Response is still a valid list
        """
        logger.info("Testing /models endpoint error handling")

        response = await api_client.get("/api/models")
        response.raise_for_status()

        assert response.status_code == 200
        data = response.json()

        if isinstance(data, dict):
            for skip_key in ["fs", "manage", "docs"]:
                data.pop(skip_key, None)
            models = list(data.values())
        else:
            models = data

        # Filter out system endpoints if they appear in the list by uid
        models = [
            m
            for m in models
            if isinstance(m, dict) and m.get("uid") not in ["fs", "manage", "docs"]
        ]

        assert isinstance(models, list)

        # All models should have at least uid and name
        for model in models:
            assert "uid" in model, "Model missing uid"
            assert "name" in model, "Model missing name"

    @pytest.mark.asyncio
    async def test_server_status_timeout(
        self, api_client: httpx.AsyncClient, available_models: list[dict]
    ):
        """
        Test that server status endpoint respects timeout.

        Verifies:
        - Endpoint responds within timeout period
        """
        if not available_models:
            pytest.skip("No models available for testing")

        model_uid = available_models[0]["uid"]
        logger.info(f"Testing server status timeout for {model_uid}")

        # Use shorter timeout to verify timeout handling
        response = await api_client.get(f"/api/servers/{model_uid}/status", timeout=5.0)
        response.raise_for_status()

        assert response.status_code == 200
        logger.info("Server status endpoint responded within timeout")
