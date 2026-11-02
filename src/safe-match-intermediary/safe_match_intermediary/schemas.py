"""Validate requests exactly as the Safe Matching API does, and allowlist responses.

Ported from semantic-match-api service/match_service/schemas.py (queries here have no
``persist``); keep the two in step. Messages name fields and limits, never values.
"""

import re

SHA256 = re.compile(r"[0-9a-fA-F]{64}")
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
CONTROL = re.compile(r"[\x00-\x1f\x7f]")
MAX_EMAIL = 254
MAX_FILE_NAME = 255
MAX_VERSION = 2**53 - 1
MAX_ESSAY_CHARS = 1000
MAX_TOP_K = 1000
DEFAULT_TOP_K = 10
UPLOAD_FIELDS = {"sha256", "investigator_email", "essay_version", "file_name", "essay"}
UPLOAD_REQUIRED = UPLOAD_FIELDS - {"file_name"}
INVESTIGATOR_FIELDS = ("email", "file_name", "first_submitted_at", "last_submitted_at")


class InvalidRequest(Exception):
    def __init__(self, message: str, fields: list[str]):
        super().__init__(message)
        self.message = message
        self.fields = fields


def _invalid(field: str, message: str) -> InvalidRequest:
    return InvalidRequest(message, [field])


def _check_fields(body: object, allowed: set[str], required: set[str]) -> dict:
    if not isinstance(body, dict):
        raise _invalid("body", "The value must be a JSON object.")
    unknown = sorted(set(body) - allowed)
    if unknown:
        raise InvalidRequest("Unknown fields are not allowed.", unknown)
    missing = sorted(required - set(body))
    if missing:
        raise InvalidRequest("Required fields are missing.", missing)
    return body


def _essay(value: object) -> str:
    essay = value.strip() if isinstance(value, str) else ""
    if not 1 <= len(essay) <= MAX_ESSAY_CHARS:
        raise _invalid("essay", f"essay must be 1 to {MAX_ESSAY_CHARS} characters.")
    return essay


def _metadata(body: dict) -> dict:
    sha256, email = body["sha256"], body["investigator_email"]
    version = body["essay_version"]
    if not isinstance(sha256, str) or not SHA256.fullmatch(sha256):
        raise _invalid("sha256", "sha256 must be 64 hexadecimal characters.")
    if (
        not isinstance(email, str)
        or len(email) > MAX_EMAIL
        or not EMAIL.fullmatch(email)
    ):
        raise _invalid(
            "investigator_email",
            f"investigator_email must be an email address of at most {MAX_EMAIL} "
            "characters.",
        )
    if type(version) is not int or not 1 <= version <= MAX_VERSION:
        raise _invalid("essay_version", "essay_version must be a positive integer.")
    return {
        "sha256": sha256.lower(),
        "investigator_email": email.lower(),
        "essay_version": version,
    }


def _file_name(body: dict) -> dict:
    if "file_name" not in body:
        return {}
    name = body["file_name"]
    if (
        not isinstance(name, str)
        or not 1 <= len(name) <= MAX_FILE_NAME
        or CONTROL.search(name)
    ):
        raise _invalid(
            "file_name",
            f"file_name must be 1 to {MAX_FILE_NAME} characters without control "
            "characters.",
        )
    return {"file_name": name}


def validate_upload(body: object) -> dict:
    """Return the normalized file metadata and stripped essay of an upload."""
    fields = _check_fields(body, UPLOAD_FIELDS, UPLOAD_REQUIRED)
    essay = _essay(fields["essay"])
    return {**_metadata(fields), **_file_name(fields), "essay": essay}


def validate_query(body: object) -> dict:
    """Return the stripped essay and top_k of a query."""
    fields = _check_fields(body, {"essay", "top_k"}, {"essay"})
    top_k = fields.get("top_k", DEFAULT_TOP_K)
    if type(top_k) is not int or not 1 <= top_k <= MAX_TOP_K:
        raise _invalid("top_k", f"top_k must be an integer from 1 to {MAX_TOP_K}.")
    return {"essay": _essay(fields["essay"]), "top_k": top_k}


def allowlist_matches(payload: dict) -> dict:
    """Rebuild a query response from known fields so nothing else reaches RescueBox."""
    return {
        "model": str(payload["model"]),
        "matches": [_match(m) for m in payload["matches"]],
    }


def _match(match: dict) -> dict:
    return {
        "sha256": match["sha256"],
        "distance": match["distance"],
        "essay_version": match["essay_version"],
        "investigators": [_investigator(item) for item in match["investigators"]],
    }


def _investigator(item: dict) -> dict:
    return {key: item[key] for key in INVESTIGATOR_FIELDS if key in item}
