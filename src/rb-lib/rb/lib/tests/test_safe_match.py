import httpx
import pytest

from rb.lib.safe_match import (
    NOT_RUNNING,
    STUB,
    WARNINGS,
    SafeMatchClient,
    SafeMatchError,
    status_warning,
)

UPLOAD = {
    "sha256": "a" * 64,
    "investigator_email": "x@example.org",
    "essay_version": 1,
    "essay": "a red bicycle",
}


def client(handler) -> SafeMatchClient:
    transport = httpx.MockTransport(handler)
    return SafeMatchClient(http=httpx.Client(transport=transport, base_url="http://sm"))


def refuse(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("refused", request=request)


def answer(status: int, code: str, fields: list[str] | None = None):
    error = {"code": code, "message": "m"}
    if fields:
        error["details"] = {"fields": fields}
    return lambda request: httpx.Response(status, json={"error": error})


def test_status_is_none_when_the_intermediary_is_down() -> None:
    assert client(refuse).status() is None
    assert (
        client(lambda r: httpx.Response(400, text="Invalid host header")).status()
        is None
    )


def test_uploads_send_only_given_fields() -> None:
    sent = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(202, json={"delivery": "queued"})

    client(handler).upload(**UPLOAD)
    assert sent[0].url.path == "/v1/upload"
    assert sent[0].headers["content-type"] == "application/json"
    assert b"file_name" not in sent[0].content


@pytest.mark.parametrize(
    "handler,code,retryable",
    [
        (refuse, "intermediary_unavailable", True),
        (answer(503, "remote_unavailable"), "remote_unavailable", True),
        (answer(503, "not_configured"), "not_configured", False),
        (answer(503, "remote_unauthorized"), "remote_unauthorized", False),
        (lambda r: httpx.Response(500, text="oops"), "intermediary_error", False),
    ],
)
def test_errors_are_typed(handler, code: str, retryable: bool) -> None:
    with pytest.raises(SafeMatchError) as raised:
        client(handler).query("a red bicycle")
    assert (raised.value.code, raised.value.retryable) == (code, retryable)


def test_rejected_fields_are_reported() -> None:
    with pytest.raises(SafeMatchError) as raised:
        client(answer(400, "invalid_request", ["sha256"])).upload(**UPLOAD)
    assert (raised.value.status, raised.value.fields) == (400, ["sha256"])


@pytest.mark.parametrize(
    "status,warning",
    [
        (None, NOT_RUNNING),
        ({"mode": "stub", "remote": "ok"}, STUB),
        ({"mode": "live", "remote": "ok"}, None),
        ({"mode": "live", "remote": "unchecked"}, None),
        *[
            ({"mode": "live", "remote": state}, text)
            for state, text in WARNINGS.items()
        ],
    ],
)
def test_each_state_has_its_warning(status: dict | None, warning: str | None) -> None:
    assert status_warning(status) == warning
