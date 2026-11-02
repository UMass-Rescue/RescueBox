import json
from pathlib import Path

import pytest

from safe_match_intermediary.config import Settings

CREDENTIALS = {
    "description": "Test server, contact ops@example.org",
    "client_id": "test-client",
    "client_secret": "test-secret-never-logged",
    "token_url": "https://test.auth.us-east-1.amazoncognito.com/oauth2/token",
    "api_url": "https://api.test.example",
    "scopes": "semantic-match/upload semantic-match/query",
}


@pytest.fixture
def credentials() -> dict:
    return dict(CREDENTIALS)


@pytest.fixture
def credentials_file(tmp_path: Path, credentials: dict) -> Path:
    path = tmp_path / "credentials.json"
    path.write_text(json.dumps(credentials))
    return path


@pytest.fixture
def live_settings(tmp_path: Path, credentials_file: Path) -> Settings:
    return Settings("live", "127.0.0.1", 8090, tmp_path, credentials_file)


@pytest.fixture
def stub_settings(tmp_path: Path) -> Settings:
    return Settings("stub", "127.0.0.1", 8090, tmp_path, tmp_path / "none.json")
