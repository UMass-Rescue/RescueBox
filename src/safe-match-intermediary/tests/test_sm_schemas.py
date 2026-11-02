"""Parity with semantic-match-api tests/test_schemas.py, at the default limits."""

import json

import pytest

from safe_match_intermediary.schemas import (
    InvalidRequest,
    allowlist_matches,
    validate_query,
    validate_upload,
)

SECRET = "sentinel-value-never-echoed"


def upload(**changes: object) -> dict:
    body = {
        "sha256": "AB" * 32,
        "investigator_email": "Alice@Example.org",
        "essay_version": 2,
        "essay": "  a red bicycle  ",
    }
    body.update(changes)
    return {k: v for k, v in body.items() if v is not None}


def rejects(validate, body: object, field: str) -> None:
    with pytest.raises(InvalidRequest) as raised:
        validate(body)
    assert field in raised.value.fields
    assert SECRET not in raised.value.message + str(raised.value.fields)


def test_upload_is_normalized() -> None:
    assert validate_upload(upload(file_name="IMG 1.jpg")) == {
        "sha256": "ab" * 32,
        "investigator_email": "alice@example.org",
        "essay_version": 2,
        "file_name": "IMG 1.jpg",
        "essay": "a red bicycle",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("sha256", SECRET),
        ("sha256", "a" * 63),
        ("sha256", "g" * 64),
        ("investigator_email", SECRET),
        ("investigator_email", "a" * 250 + "@x.org"),
        ("investigator_email", "a\x1c@b.c"),
        ("essay_version", 0),
        ("essay_version", True),
        ("essay_version", 1.0),
        ("essay_version", 2**53),
        ("essay_version", "1"),
        ("file_name", ""),
        ("file_name", "x" * 256),
        ("file_name", SECRET + "\n"),
        ("file_name", "x\x7f"),
        ("essay", "   "),
        ("essay", "\x1c"),
        ("essay", SECRET * 40),
        ("essay", 5),
    ],
)
def test_upload_rejects_like_the_remote(field: str, value: object) -> None:
    rejects(validate_upload, upload(**{field: value}), field)


def test_upload_rejects_unknown_and_missing_fields() -> None:
    rejects(validate_upload, upload(extra=SECRET), "extra")
    rejects(validate_upload, upload(essay_version=None), "essay_version")
    rejects(validate_upload, SECRET, "body")


def test_query_defaults_limits_and_no_persist() -> None:
    assert validate_query({"essay": " x "}) == {"essay": "x", "top_k": 10}
    assert validate_query({"essay": "x", "top_k": 1000})["top_k"] == 1000
    for top_k in (0, 1001, True, 2.0):
        rejects(validate_query, {"essay": "x", "top_k": top_k}, "top_k")
    rejects(validate_query, {"essay": "x", "persist": upload(essay=None)}, "persist")


def test_query_response_is_rebuilt_from_known_fields() -> None:
    investigator = {
        "email": "a@b.org",
        "first_submitted_at": "2026-10-01T12:00:00Z",
        "last_submitted_at": "2026-10-02T08:30:00Z",
        "client_id": SECRET,
    }
    match = {"sha256": "a" * 64, "distance": 0.07, "essay_version": 3, "essay": SECRET}
    payload = {"model": "m", "vector": [SECRET], "matches": [match]}
    match["investigators"] = [investigator]
    rebuilt = allowlist_matches(payload)
    assert SECRET not in json.dumps(rebuilt)
    assert rebuilt["matches"][0]["investigators"][0]["email"] == "a@b.org"
