"""Settings from the environment and the UMass client credentials file."""

import json
import os
import platform
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

PREFIX = "RESCUEBOX_SAFE_MATCH_"
SCOPES = "semantic-match/upload semantic-match/query"
REQUIRED = ("client_id", "client_secret", "token_url", "api_url")
COGNITO_HOST = re.compile(r"[a-z0-9-]+\.auth\.[a-z0-9-]+\.amazoncognito\.com")


def default_data_dir() -> Path:
    """Beside the other RescueBox data, as in frontend/config.py."""
    if platform.system() == "Windows":
        local = os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(local) / "RescueBox" / "safe-match"
    return Path.home() / ".rescuebox" / "safe-match"


@dataclass(frozen=True)
class Settings:
    mode: Literal["live", "stub"]
    host: str
    port: int
    data_dir: Path
    credentials_path: Path

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        mode = env.get(PREFIX + "MODE", "live")
        if mode not in ("live", "stub"):
            raise SystemExit(f"{PREFIX}MODE must be live or stub.")
        data_dir = Path(env.get(PREFIX + "DATA_DIR") or default_data_dir())
        credentials = env.get(PREFIX + "CREDENTIALS") or data_dir / "credentials.json"
        host = env.get(PREFIX + "HOST", "127.0.0.1")
        port = int(env.get(PREFIX + "PORT", "8090"))
        return cls(mode, host, port, data_dir, Path(credentials))


@dataclass(frozen=True)
class Credentials:
    client_id: str
    client_secret: str = field(repr=False)
    token_url: str
    api_url: str
    scopes: str = SCOPES


class CredentialsError(Exception):
    """Missing or invalid credentials; messages name fields, never values."""

    def __init__(self, reason: Literal["missing", "invalid"], message: str):
        super().__init__(message)
        self.reason = reason


def load_credentials(path: Path) -> Credentials:
    """Read the file that semantic-match-api tools/clients.py writes for a server."""
    data = _read(path)
    if not all(isinstance(data.get(key), str) and data[key] for key in REQUIRED):
        needed = ", ".join(REQUIRED)
        raise CredentialsError("invalid", f"The credentials file needs {needed}.")
    _check_url(data["api_url"], "api_url")
    _check_url(data["token_url"], "token_url")
    token_url = urlsplit(data["token_url"])
    if not COGNITO_HOST.fullmatch(token_url.hostname or "") or (
        token_url.path != "/oauth2/token"
    ):
        raise CredentialsError("invalid", "token_url must be a Cognito token address.")
    return Credentials(
        data["client_id"],
        data["client_secret"],
        data["token_url"],
        data["api_url"].rstrip("/"),
        data.get("scopes") or SCOPES,
    )


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise CredentialsError("missing", f"No credentials file at {path}.") from None
    except (OSError, ValueError):
        raise CredentialsError(
            "invalid", "The credentials file is unreadable."
        ) from None
    if not isinstance(data, dict):
        raise CredentialsError("invalid", "The credentials file must hold an object.")
    return data


def _check_url(value: str, name: str) -> None:
    url = urlsplit(value)
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise CredentialsError("invalid", f"{name} must be an https address.")
    if url.query or url.fragment:
        raise CredentialsError("invalid", f"{name} must not have a query or fragment.")
