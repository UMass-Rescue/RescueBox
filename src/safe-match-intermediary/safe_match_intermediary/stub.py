"""In-process stand-in for Cognito and the Safe Matching API, for stub mode and tests."""

import json
import re
from datetime import datetime, timezone

import httpx

from .config import Credentials

STUB_CREDENTIALS = Credentials(
    client_id="stub-client",
    client_secret="stub-secret",
    token_url="https://stub.auth.us-east-1.amazoncognito.com/oauth2/token",
    api_url="https://stub.safe-match.invalid",
)
WORD = re.compile(r"[a-z0-9]+")


class FakeApi:
    """Keeps uploads in memory under the API's ingest rules; ranks by word overlap."""

    def __init__(self) -> None:
        self.essays: dict[str, tuple[int, str]] = {}
        self.investigators: dict[str, dict[str, dict]] = {}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/oauth2/token":
            token = {"access_token": "stub-token", "expires_in": 86400}
            return httpx.Response(200, json=token)
        if path == "/v1/upload":
            return httpx.Response(202, json=self.upload(json.loads(request.content)))
        if path == "/v1/query":
            return httpx.Response(200, json=self.query(json.loads(request.content)))
        return httpx.Response(404, json={"error": {"code": "not_found", "message": ""}})

    def upload(self, body: dict) -> dict:
        sha256, version = body["sha256"], body["essay_version"]
        stored = self.essays.get(sha256)
        updated = stored is None or version > stored[0]
        if updated:
            self.essays[sha256] = (version, body["essay"])
        self._record_investigator(body)
        stored_version = self.essays[sha256][0]
        return {
            "sha256": sha256,
            "essay_version": stored_version,
            "essay_updated": updated,
            "indexing": "current",
        }

    def query(self, body: dict) -> dict:
        words = _words(body["essay"])
        ranked = sorted(
            (_distance(words, _words(essay)), sha256)
            for sha256, (_, essay) in self.essays.items()
        )
        top = ranked[: body.get("top_k", 10)]
        return {"model": "stub", "matches": [self._match(s, d) for d, s in top]}

    def _record_investigator(self, body: dict) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        email = body["investigator_email"]
        rows = self.investigators.setdefault(body["sha256"], {})
        row = rows.setdefault(email, {"email": email, "first_submitted_at": now})
        row["last_submitted_at"] = now
        if "file_name" in body:
            row["file_name"] = body["file_name"]

    def _match(self, sha256: str, distance: float) -> dict:
        return {
            "sha256": sha256,
            "distance": round(distance, 4),
            "essay_version": self.essays[sha256][0],
            "investigators": list(self.investigators[sha256].values()),
        }


def _words(text: str) -> set[str]:
    return set(WORD.findall(text.lower()))


def _distance(a: set[str], b: set[str]) -> float:
    union = a | b
    return 1 - len(a & b) / len(union) if union else 1.0
