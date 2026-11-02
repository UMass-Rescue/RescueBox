"""Client for the UMass Safe Matching API: tokens, uploads, queries and error kinds."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Literal

import httpx

from .config import Credentials
from .schemas import allowlist_matches

logger = logging.getLogger(__name__)
Kind = Literal["rejected", "unauthorized", "forbidden", "unavailable"]
REJECTED = {(400, "invalid_request"), (413, "payload_too_large")}
FAST_RETRY = {429, 502, 503, 504}
MAX_RETRY_AFTER = 300.0
QUERY_RETRY_WINDOW = 10.0


class RemoteError(Exception):
    """A failed API call, described without request content."""

    def __init__(
        self,
        kind: Kind,
        status: int | None = None,
        error: dict | None = None,
        retry_after: float | None = None,
        fast: bool = False,
    ):
        super().__init__(kind)
        error = error or {}
        details = error.get("details")
        self.kind, self.status, self.retry_after, self.fast = (
            kind,
            status,
            retry_after,
            fast,
        )
        self.code = str(error.get("code", "remote_error"))
        self.message = str(error.get("message", "The Safe Matching service failed."))
        self.fields = (
            list(details.get("fields", [])) if isinstance(details, dict) else []
        )
        self.request_id = error.get("request_id")


def classify(response: httpx.Response) -> RemoteError:
    """Only invalid or oversized requests are the request's fault; all else pauses."""
    error = _service_error(response)
    status = response.status_code
    if (status, error.get("code")) in REJECTED:
        return RemoteError("rejected", status, error)
    kind = {401: "unauthorized", 403: "forbidden"}.get(status, "unavailable")
    return RemoteError(
        kind, status, error, _retry_after(response), status in FAST_RETRY
    )


def _service_error(response: httpx.Response) -> dict:
    try:
        error = response.json()["error"]
    except (ValueError, KeyError, TypeError):
        return {}
    return error if isinstance(error, dict) else {}


def _retry_after(response: httpx.Response) -> float | None:
    try:
        return min(float(response.headers["Retry-After"]), MAX_RETRY_AFTER)
    except (KeyError, ValueError):
        return None


def _network_error(error: httpx.HTTPError) -> RemoteError:
    return RemoteError("unavailable", fast=isinstance(error, httpx.ConnectError))


class TokenProvider:
    """Exchange the client credentials for access tokens, reusing each until near expiry."""

    def __init__(
        self,
        credentials: Credentials,
        http: httpx.AsyncClient,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.credentials, self.http, self.clock = credentials, http, clock
        self.lock = asyncio.Lock()
        self.token: str | None = None
        self.refresh_at = 0.0

    async def get(self) -> str:
        async with self.lock:
            if self.token is None or self.clock() >= self.refresh_at:
                self.token, lifetime = await self._fetch()
                self.refresh_at = self.clock() + max(lifetime - 300, lifetime / 2)
            return self.token

    def invalidate(self, token: str) -> None:
        """Forget a rejected token unless another caller already replaced it."""
        if token == self.token:
            self.token = None

    async def _fetch(self) -> tuple[str, float]:
        grant = {"grant_type": "client_credentials", "scope": self.credentials.scopes}
        secret = (self.credentials.client_id, self.credentials.client_secret)
        try:
            response = await self.http.post(
                self.credentials.token_url, data=grant, auth=secret
            )
        except httpx.HTTPError as error:
            raise _network_error(error) from None
        if response.status_code in (400, 401):
            raise RemoteError("unauthorized", response.status_code)
        if response.status_code != 200:
            raise RemoteError("unavailable", response.status_code)
        return _token(response)


def _token(response: httpx.Response) -> tuple[str, float]:
    try:
        payload = response.json()
        token, lifetime = payload["access_token"], payload["expires_in"]
    except (ValueError, KeyError, TypeError):
        raise RemoteError("unavailable", response.status_code) from None
    if not isinstance(token, str) or not token or type(lifetime) is not int:
        raise RemoteError("unavailable", response.status_code)
    if lifetime <= 0:
        raise RemoteError("unavailable", response.status_code)
    return token, float(lifetime)


class Remote:
    """Upload and query, refreshing the token once when a request gets 401."""

    def __init__(
        self,
        credentials: Credentials,
        http: httpx.AsyncClient,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ):
        self.url, self.http, self.clock, self.sleep = (
            credentials.api_url,
            http,
            clock,
            sleep,
        )
        self.tokens = TokenProvider(credentials, http, clock)
        self.state = "unchecked"

    async def check(self) -> None:
        """Fetch a token at startup so the status shows whether the credentials work."""
        try:
            await self.tokens.get()
        except RemoteError as error:
            self._record(error.kind)
            return
        self._record("ok")

    async def upload(self, item: dict) -> None:
        await self._call("/v1/upload", item, 202)

    async def query(self, item: dict) -> dict:
        """Retry once only after a fast, transient failure; a slow one used the time."""
        started = self.clock()
        try:
            response = await self._call("/v1/query", item, 200)
        except RemoteError as error:
            if not error.fast or self.clock() - started >= QUERY_RETRY_WINDOW:
                raise
            await self.sleep(min(error.retry_after or 1.0, 5.0))
            response = await self._call("/v1/query", item, 200)
        try:
            return allowlist_matches(response.json())
        except (ValueError, KeyError, TypeError):
            raise RemoteError("unavailable", response.status_code) from None

    async def _call(self, path: str, body: dict, expected: int) -> httpx.Response:
        try:
            response = await self._send(path, body)
            if response.status_code != expected:
                raise classify(response)
        except RemoteError as error:
            self._record("ok" if error.kind == "rejected" else error.kind)
            raise
        self._record("ok")
        return response

    async def _send(self, path: str, body: dict) -> httpx.Response:
        token = await self.tokens.get()
        response = await self._post(path, body, token)
        if response.status_code != 401:
            return response
        self.tokens.invalidate(token)
        return await self._post(path, body, await self.tokens.get())

    async def _post(self, path: str, body: dict, token: str) -> httpx.Response:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            return await self.http.post(self.url + path, json=body, headers=headers)
        except httpx.HTTPError as error:
            raise _network_error(error) from None

    def _record(self, state: str) -> None:
        if state != self.state:
            logger.info("remote_state %s", state)
        self.state = state
