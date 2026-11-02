import asyncio
import base64
from collections.abc import AsyncIterator, Callable

import httpx
import pytest

from safe_match_intermediary.remote import Remote, RemoteError, TokenProvider, classify
from safe_match_intermediary.stub import STUB_CREDENTIALS, FakeApi

ITEM = {
    "sha256": "a" * 64,
    "investigator_email": "x@example.org",
    "essay_version": 1,
    "essay": "a red bicycle by a brick wall",
}
QUERY = {"essay": "a red bike by a wall", "top_k": 10}


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class Sleeps(list):
    async def __call__(self, seconds: float) -> None:
        self.append(seconds)


class Recorder:
    """Serve requests with a handler and keep them for inspection."""

    def __init__(self, handler: Callable[[httpx.Request], httpx.Response]):
        self.handler, self.requests = handler, []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.handler(request)

    def count(self, path: str) -> int:
        return sum(request.url.path == path for request in self.requests)


@pytest.fixture
async def http() -> AsyncIterator[Callable[[Recorder], httpx.AsyncClient]]:
    clients: list[httpx.AsyncClient] = []

    def make(handler: Recorder) -> httpx.AsyncClient:
        clients.append(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        return clients[-1]

    yield make
    for client in clients:
        await client.aclose()


def failing(path: str, *responses: httpx.Response) -> Recorder:
    """FakeApi, except that requests to path get the given responses first."""
    api, queue = FakeApi(), list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == path and queue:
            return queue.pop(0)
        return api(request)

    return Recorder(handler)


def error(status: int, code: str) -> httpx.Response:
    return httpx.Response(status, json={"error": {"code": code, "message": "m"}})


@pytest.mark.parametrize(
    "response,kind",
    [
        (error(400, "invalid_request"), "rejected"),
        (error(413, "payload_too_large"), "rejected"),
        (error(400, "invalid_json"), "unavailable"),
        (httpx.Response(400, json={"message": "Bad Request"}), "unavailable"),
        (httpx.Response(401, json={"message": "Unauthorized"}), "unauthorized"),
        (error(403, "forbidden"), "forbidden"),
        (error(404, "not_found"), "unavailable"),
        (httpx.Response(429, json={"message": "Too Many Requests"}), "unavailable"),
        (error(500, "internal_error"), "unavailable"),
    ],
)
def test_only_bad_requests_are_rejected(response: httpx.Response, kind: str) -> None:
    assert classify(response).kind == kind


def test_retry_after_is_read_and_capped() -> None:
    assert classify(httpx.Response(503, headers={"Retry-After": "1"})).retry_after == 1
    assert (
        classify(httpx.Response(503, headers={"Retry-After": "900"})).retry_after == 300
    )
    assert classify(httpx.Response(503)).fast and not classify(error(500, "x")).fast


async def test_token_is_reused_until_the_refresh_margin(http) -> None:
    api, clock = Recorder(FakeApi()), Clock()
    tokens = TokenProvider(STUB_CREDENTIALS, http(api), clock)
    await tokens.get()
    clock.now = 86400 - 301
    await tokens.get()
    assert api.count("/oauth2/token") == 1
    clock.now = 86400 - 299
    await tokens.get()
    assert api.count("/oauth2/token") == 2


async def test_concurrent_401s_cause_one_refresh(http) -> None:
    issued = iter(["t1", "t2", "t3"])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/token":
            return httpx.Response(
                200, json={"access_token": next(issued), "expires_in": 86400}
            )
        stale = request.headers["Authorization"] == "Bearer t1"
        return httpx.Response(401 if stale else 202, json={})

    api = Recorder(handler)
    remote = Remote(STUB_CREDENTIALS, http(api), Clock())
    await asyncio.gather(*(remote.upload(ITEM) for _ in range(5)))
    assert api.count("/oauth2/token") == 2


async def test_a_401_refreshes_once_then_reports_unauthorized(http) -> None:
    api = failing("/v1/upload", *[httpx.Response(401, json={})] * 2)
    remote = Remote(STUB_CREDENTIALS, http(api), Clock())
    with pytest.raises(RemoteError) as raised:
        await remote.upload(ITEM)
    assert raised.value.kind == "unauthorized" and remote.state == "unauthorized"
    assert (api.count("/oauth2/token"), api.count("/v1/upload")) == (2, 2)


async def test_rejected_credentials_show_in_the_state(http) -> None:
    api = failing(
        "/oauth2/token", httpx.Response(400, json={"error": "invalid_client"})
    )
    remote = Remote(STUB_CREDENTIALS, http(api), Clock())
    await remote.check()
    assert remote.state == "unauthorized"


async def test_the_secret_goes_only_to_the_token_url(http) -> None:
    api = Recorder(FakeApi())
    remote = Remote(STUB_CREDENTIALS, http(api), Clock())
    await remote.upload(ITEM)
    await remote.query(QUERY)
    pair = f"{STUB_CREDENTIALS.client_id}:{STUB_CREDENTIALS.client_secret}"
    basic = "Basic " + base64.b64encode(pair.encode()).decode()
    for request in api.requests:
        is_token = str(request.url) == STUB_CREDENTIALS.token_url
        assert (request.headers["Authorization"] == basic) == is_token
        assert STUB_CREDENTIALS.client_secret.encode() not in request.content


async def test_a_query_retries_one_fast_failure(http) -> None:
    busy = httpx.Response(503, headers={"Retry-After": "1"}, json={})
    api, sleeps = failing("/v1/query", busy), Sleeps()
    remote = Remote(STUB_CREDENTIALS, http(api), Clock(), sleeps)
    await remote.upload(ITEM)
    assert (await remote.query(QUERY))["matches"][0]["sha256"] == ITEM["sha256"]
    assert (api.count("/v1/query"), sleeps) == (2, [1.0])


async def test_a_query_is_not_retried_after_a_read_timeout(http) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/query":
            raise httpx.ReadTimeout("timed out", request=request)
        return FakeApi()(request)

    api = Recorder(handler)
    remote = Remote(STUB_CREDENTIALS, http(api), Clock(), Sleeps())
    with pytest.raises(RemoteError) as raised:
        await remote.query(QUERY)
    assert raised.value.kind == "unavailable" and api.count("/v1/query") == 1
