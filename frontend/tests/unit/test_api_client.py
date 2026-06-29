"""Unit tests for frontend.api_client.ApiClient."""

from __future__ import annotations

import httpx
import pytest
from unittest.mock import AsyncMock, Mock, patch

from frontend.api_client import ApiClient


@pytest.fixture
def client():
    return ApiClient("http://127.0.0.1:8000/api", timeout=5)


class TestApiClientPaths:
    def test_make_api_path_adds_prefix_when_base_has_no_api_suffix(self):
        c = ApiClient("http://127.0.0.1:8000", timeout=1)
        assert c._make_api_path("audio/transcribe") == "/api/audio/transcribe"
        assert c._make_api_path("/audio/transcribe") == "/api/audio/transcribe"

    def test_make_api_path_no_double_prefix_when_base_ends_with_api(self, client):
        assert client._make_api_path("audio/transcribe") == "/audio/transcribe"


class TestApiClientJson:
    @pytest.mark.asyncio
    async def test_json_returns_dict_from_sync_response(self, client):
        response = Mock(spec=httpx.Response)
        response.json = Mock(return_value={"ok": True})
        data = await client.json(response)
        assert data == {"ok": True}

    @pytest.mark.asyncio
    async def test_json_awaits_coroutine_function_json(self, client):
        response = Mock(spec=httpx.Response)

        async def _async_json():
            return {"from": "async"}

        response.json = _async_json
        data = await client.json(response)
        assert data == {"from": "async"}

    @pytest.mark.asyncio
    async def test_json_awaits_coroutine_return_value(self, client):
        response = Mock(spec=httpx.Response)

        async def _payload():
            return {"nested": 1}

        response.json = Mock(return_value=_payload())
        data = await client.json(response)
        assert data == {"nested": 1}

    @pytest.mark.asyncio
    async def test_json_callable_mock_returns_value(self, client):
        response = Mock(spec=httpx.Response)
        inner = Mock(return_value={"via": "callable"})
        response.json = Mock(return_value=inner)
        data = await client.json(response)
        assert data == {"via": "callable"}


class TestApiClientHttp:
    @pytest.mark.asyncio
    async def test_get_uses_async_client_when_sync_not_patched(self, client):
        mock_resp = Mock(spec=httpx.Response)
        client._client.get = AsyncMock(return_value=mock_resp)
        with patch.object(httpx, "Client", httpx.Client):
            out = await client.get("test/endpoint", use_api_prefix=False)
        assert out is mock_resp
        client._client.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_post_uses_sync_mock_when_client_class_patched(self, client):
        mock_resp = Mock(spec=httpx.Response)
        sync = Mock()
        sync.post = Mock(return_value=mock_resp)
        sync.__enter__ = Mock(return_value=sync)
        sync.__exit__ = Mock(return_value=False)
        with patch.object(httpx, "Client", Mock(return_value=sync)):
            out = await client.post("/job", json={"a": 1}, use_api_prefix=False)
        assert out is mock_resp
        sync.post.assert_called_once()
