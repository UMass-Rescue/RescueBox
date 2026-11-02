import json
import logging
import time
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from rb.lib.safe_match import (
    NOT_RUNNING,
    STUB,
    WARNINGS,
    SafeMatchClient,
    status_warning,
)
from safe_match_intermediary.app import create_app
from safe_match_intermediary.config import Settings
from safe_match_intermediary.stub import FakeApi

SECRET = "sentinel-value-never-echoed"
UPLOAD = {
    "sha256": "a" * 64,
    "investigator_email": "x@example.org",
    "essay_version": 1,
    "essay": "A red bicycle leans against a brick wall beside a wooden door.",
}
UNRELATED = {
    **UPLOAD,
    "sha256": "b" * 64,
    "essay": "A bowl of oranges sits on a kitchen table under a window.",
}
PARAPHRASE = "A red bike rests against a brick wall next to a door."


def serve(
    settings: Settings, transport: httpx.MockTransport | None = None
) -> TestClient:
    return TestClient(create_app(settings, transport), base_url="http://127.0.0.1")


def wait_until(condition: Callable[[], bool], seconds: float = 2.0) -> None:
    deadline = time.monotonic() + seconds
    while not condition():
        assert time.monotonic() < deadline, "condition not met in time"
        time.sleep(0.01)


def on_query(
    response: Callable[[httpx.Request], httpx.Response],
) -> httpx.MockTransport:
    api = FakeApi()

    def handler(request: httpx.Request) -> httpx.Response:
        return response(request) if request.url.path == "/v1/query" else api(request)

    return httpx.MockTransport(handler)


def test_bodies_must_be_declared_json(stub_settings: Settings) -> None:
    with serve(stub_settings) as client:
        for headers in ({}, {"content-type": "text/plain"}):
            response = client.post(
                "/v1/upload", content=json.dumps(UPLOAD), headers=headers
            )
            assert response.status_code == 415
        assert client.get("/v1/status").json()["outbox"] == {"pending": 0, "failed": 0}


def test_other_hosts_and_large_bodies_are_refused(stub_settings: Settings) -> None:
    with serve(stub_settings) as client:
        assert (
            client.get("/v1/status", headers={"host": "evil.example"}).status_code
            == 400
        )
        large = {**UPLOAD, "essay": "x" * 70_000}
        assert client.post("/v1/upload", json=large).status_code == 413


def test_invalid_fields_are_named_not_echoed(stub_settings: Settings) -> None:
    with serve(stub_settings) as client:
        response = client.post("/v1/upload", json={**UPLOAD, "essay_version": SECRET})
    assert response.status_code == 400
    assert response.json()["error"]["details"] == {"fields": ["essay_version"]}
    assert SECRET not in response.text


def test_without_credentials_requests_are_refused(tmp_path: Path) -> None:
    settings = Settings("live", "127.0.0.1", 8090, tmp_path, tmp_path / "absent.json")
    with serve(settings) as client:
        status = client.get("/v1/status").json()
        upload = client.post("/v1/upload", json=UPLOAD)
        query = client.post("/v1/query", json={"essay": PARAPHRASE})
    assert (status["configured"], status["remote"]) == (False, "credentials_missing")
    assert (upload.status_code, upload.json()["error"]["code"]) == (
        503,
        "not_configured",
    )
    assert query.status_code == 503


def test_query_responses_carry_only_known_fields(live_settings: Settings) -> None:
    api = FakeApi()
    api.upload(UPLOAD)

    def leaky(request: httpx.Request) -> httpx.Response:
        payload = api.query(json.loads(request.content))
        payload["matches"][0]["essay"] = SECRET
        payload["matches"][0]["investigators"][0]["client_id"] = SECRET
        return httpx.Response(200, json=payload)

    with serve(live_settings, on_query(leaky)) as client:
        response = client.post("/v1/query", json={"essay": PARAPHRASE})
    assert response.json()["matches"][0]["sha256"] == UPLOAD["sha256"]
    assert SECRET not in response.text


@pytest.mark.parametrize(
    "remote,body,status,code",
    [
        (
            400,
            {"error": {"code": "invalid_request", "message": "m"}},
            400,
            "invalid_request",
        ),
        (401, {"message": "Unauthorized"}, 503, "remote_unauthorized"),
        (403, {"message": "Forbidden"}, 503, "remote_forbidden"),
        (500, {"message": "Internal"}, 503, "remote_unavailable"),
    ],
)
def test_remote_errors_map_to_local_errors(
    live_settings: Settings, remote: int, body: dict, status: int, code: str
) -> None:
    reply = on_query(lambda request: httpx.Response(remote, json=body))
    with serve(live_settings, reply) as client:
        response = client.post("/v1/query", json={"essay": PARAPHRASE})
        state = client.get("/v1/status").json()["remote"]
    assert (response.status_code, response.json()["error"]["code"]) == (status, code)
    assert state == {400: "ok"}.get(status, code.removeprefix("remote_"))


def test_sensitive_values_never_reach_the_logs(
    live_settings: Settings, credentials: dict, caplog: pytest.LogCaptureFixture
) -> None:
    def broken(request: httpx.Request) -> httpx.Response:
        raise RuntimeError(json.loads(request.content)["essay"])

    caplog.set_level(logging.DEBUG)
    secret_upload = {**UPLOAD, "investigator_email": f"{SECRET}@example.org"}
    with serve(live_settings, on_query(broken)) as client:
        assert client.post(
            "/v1/upload", json={**secret_upload, "essay": SECRET}
        ).is_success
        wait_until(lambda: client.get("/v1/status").json()["outbox"]["pending"] == 0)
        response = client.post("/v1/query", json={"essay": SECRET})
    assert (response.status_code, response.json()["error"]["code"]) == (
        500,
        "internal_error",
    )
    assert "RuntimeError" in caplog.text
    for value in (SECRET, credentials["client_secret"], "stub-token"):
        assert value not in caplog.text


def test_stub_mode_keeps_no_files(stub_settings: Settings, tmp_path: Path) -> None:
    with serve(stub_settings) as client:
        SafeMatchClient(http=client).upload(**UPLOAD)
    assert list(tmp_path.iterdir()) == []


def test_sdk_round_trip_in_stub_mode(stub_settings: Settings) -> None:
    with serve(stub_settings) as client:
        sdk = SafeMatchClient(http=client)
        sdk.upload(**UPLOAD, file_name="IMG_0001.jpg")
        sdk.upload(**UNRELATED)
        wait_until(lambda: sdk.status()["outbox"]["pending"] == 0)
        best = sdk.query(PARAPHRASE, top_k=2)["matches"][0]
    assert best["sha256"] == UPLOAD["sha256"]
    assert best["investigators"][0]["file_name"] == "IMG_0001.jpg"


def test_sdk_warnings_match_the_server_states(
    stub_settings: Settings, tmp_path: Path
) -> None:
    with serve(stub_settings) as client:
        assert status_warning(SafeMatchClient(http=client).status()) == STUB
    missing = Settings("live", "127.0.0.1", 8090, tmp_path, tmp_path / "absent.json")
    with serve(missing) as client:
        status = SafeMatchClient(http=client).status()
    assert status_warning(status) == WARNINGS["credentials_missing"]
    assert status_warning(
        SafeMatchClient("http://127.0.0.1:9", timeout=2).status()
    ) == (NOT_RUNNING)
