"""Client SDK for the Safe Match intermediary, called in-process by plugins.

The intermediary (src/safe-match-intermediary) is the only RescueBox component that
talks to the UMass Safe Matching service. Plugins reach it on loopback, the way the
frontend reaches the backend.

Usage:
    from rb.lib.safe_match import SafeMatchClient, status_warning
    client = SafeMatchClient()
    warning = status_warning(client.status())  # show in a task_schema subtitle
    client.upload(sha256=..., investigator_email=..., essay_version=1, essay=...)
    matches = client.query(essay, top_k=10)["matches"]
"""

import os

import httpx

SAFE_MATCH_PORT = int(os.getenv("RESCUEBOX_SAFE_MATCH_PORT", "8090"))
SAFE_MATCH_URL = os.getenv(
    "RESCUEBOX_SAFE_MATCH_URL", f"http://127.0.0.1:{SAFE_MATCH_PORT}"
)
SAFE_MATCH_TIMEOUT = float(os.getenv("RESCUEBOX_SAFE_MATCH_TIMEOUT", "60"))

RETRYABLE = {"intermediary_unavailable", "remote_unavailable"}
NOT_RUNNING = (
    "Safe Match is not enabled, so essays are not sent to UMass. "
    "Ask your administrator to configure access."
)
STUB = "Safe Match is in stub mode: nothing is sent to UMass and matches are simulated."
WARNINGS = {
    "credentials_missing": "Safe Match has no UMass credentials. "
    "Ask your administrator to configure access.",
    "credentials_invalid": "Safe Match's UMass credentials are invalid. "
    "Ask your administrator to replace them.",
    "unauthorized": "UMass rejected this server's Safe Match credentials. "
    "Ask your administrator.",
    "forbidden": "This server's Safe Match credentials lack a needed permission. "
    "Ask your administrator.",
    "unavailable": "UMass Safe Matching is unreachable; "
    "essays are queued and will be sent later.",
}


class SafeMatchError(Exception):
    """A failed call; code tells intermediary, UMass and request problems apart."""

    def __init__(
        self,
        code: str,
        message: str,
        status: int | None = None,
        fields: list[str] | None = None,
    ):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status
        self.fields = fields or []

    @property
    def retryable(self) -> bool:
        return self.code in RETRYABLE


class SafeMatchClient:
    """Thin synchronous wrapper with one method per intermediary endpoint."""

    def __init__(
        self,
        base_url: str = SAFE_MATCH_URL,
        timeout: float = SAFE_MATCH_TIMEOUT,
        http: httpx.Client | None = None,
    ):
        self.http = http or httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    def status(self) -> dict | None:
        """The intermediary's status, or None when it is not running."""
        try:
            response = self.http.get("/v1/status")
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError):
            return None

    def upload(
        self,
        *,
        sha256: str,
        investigator_email: str,
        essay_version: int,
        essay: str,
        file_name: str | None = None,
    ) -> None:
        """Queue an essay for delivery to UMass; returns once it is stored durably."""
        body = {
            "sha256": sha256,
            "investigator_email": investigator_email,
            "essay_version": essay_version,
            "essay": essay,
        }
        if file_name is not None:
            body["file_name"] = file_name
        self._post("/v1/upload", body)

    def query(self, essay: str, top_k: int = 10) -> dict:
        """Metadata of the files whose essays are closest to this one."""
        return self._post("/v1/query", {"essay": essay, "top_k": top_k})

    def close(self) -> None:
        self.http.close()

    def _post(self, path: str, body: dict) -> dict:
        try:
            response = self.http.post(path, json=body)
        except httpx.HTTPError:
            message = "The Safe Match intermediary is not running."
            raise SafeMatchError("intermediary_unavailable", message) from None
        if response.is_success:
            return response.json()
        raise _error(response)


def _error(response: httpx.Response) -> SafeMatchError:
    try:
        error = response.json()["error"]
        fields = error.get("details", {}).get("fields")
        return SafeMatchError(
            error["code"], error["message"], response.status_code, fields
        )
    except (ValueError, KeyError, TypeError, AttributeError):
        message = f"The intermediary answered HTTP {response.status_code}."
        return SafeMatchError("intermediary_error", message, response.status_code)


def status_warning(status: dict | None) -> str | None:
    """Text for a plugin's task_schema subtitle, or None when Safe Match works."""
    if status is None:
        return NOT_RUNNING
    if status.get("mode") == "stub":
        return STUB
    return WARNINGS.get(status.get("remote", ""))
