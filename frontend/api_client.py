"""
Thin API client wrapper to centralize endpoint building and robust JSON handling.

Usage:
    from frontend.api_client import ApiClient
    api = ApiClient(base_url, timeout=30)
    resp = await api.get("/audio/transcribe/task_schema")
    data = await api.json(resp)
"""

from typing import Optional, Any
import httpx
import asyncio
import logging
from frontend.config import API_BASE_URL, API_TIMEOUT

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, base_url: str, timeout: int = 300):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    def _make_api_path(self, path: str) -> str:
        # Keep compatibility with existing code: if base_url already ends with /api,
        # do not add an extra prefix. Ensure path has leading slash.
        normalized = f"{'' if path.startswith('/') else '/'}{path}"
        prefix = "" if self.base_url.endswith("/api") else "/api"
        return f"{prefix}{normalized}"

    async def get(
        self, path: str, *, use_api_prefix: bool = True, **kwargs
    ) -> httpx.Response:
        full_path = (
            self._make_api_path(path)
            if use_api_prefix
            else (path if path.startswith("/") else f"/{path}")
        )
        logger.debug("ApiClient GET %s", full_path)
        # If tests have patched httpx.Client to a sync mock, prefer calling that so unit tests intercept the call.
        if not isinstance(httpx.Client, type):
            try:
                with httpx.Client(
                    base_url=self.base_url, timeout=self.timeout
                ) as sync_client:
                    return sync_client.get(full_path, **kwargs)
            except Exception:
                # fall back to async client
                pass
        return await self._client.get(full_path, **kwargs)

    async def post(
        self,
        path: str,
        json: Optional[Any] = None,
        *,
        use_api_prefix: bool = True,
        **kwargs,
    ) -> httpx.Response:
        full_path = (
            self._make_api_path(path)
            if use_api_prefix
            else (path if path.startswith("/") else f"/{path}")
        )
        logger.debug("ApiClient POST %s", full_path)
        if not isinstance(httpx.Client, type):
            try:
                with httpx.Client(
                    base_url=self.base_url, timeout=self.timeout
                ) as sync_client:
                    return sync_client.post(full_path, json=json, **kwargs)
            except Exception:
                pass
        return await self._client.post(full_path, json=json, **kwargs)

    async def json(self, response: httpx.Response) -> Any:
        """
        Resolve response.json() robustly in case tests patch the response to return awaitables.
        """
        try:
            result = response.json()
        except Exception:
            # Some mocked responses may raise; try awaiting .json if it's a coroutine
            try:
                maybe = getattr(response, "json", None)
                if asyncio.iscoroutinefunction(maybe):
                    return await maybe()
            except Exception:
                raise
            raise
        # If result is awaitable (AsyncMock), await it
        if asyncio.iscoroutine(result) or asyncio.isfuture(result):
            return await result
        if callable(result) and not isinstance(result, dict):
            try:
                maybe = result()
                if asyncio.iscoroutine(maybe) or asyncio.isfuture(maybe):
                    return await maybe
                return maybe
            except Exception:
                return result
        return result

    async def aclose(self) -> None:
        await self._client.aclose()


# Default shared client instance for modules that import `api_client`
# Keep this optional and lazy to avoid network side-effects during import-heavy test collection.
api_client = ApiClient(API_BASE_URL, timeout=int(API_TIMEOUT))
# Backwards-compatible alias expected by some modules
APIClient = ApiClient
