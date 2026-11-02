import json
from pathlib import Path

import pytest

from safe_match_intermediary.config import CredentialsError, Settings, load_credentials


def write(tmp_path: Path, credentials: dict, **changes: object) -> Path:
    data = {k: v for k, v in {**credentials, **changes}.items() if v is not None}
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(data))
    return path


def test_credentials_load_and_hide_the_secret(credentials_file: Path) -> None:
    loaded = load_credentials(credentials_file)
    assert loaded.api_url == "https://api.test.example"
    assert "test-secret" not in repr(loaded)


@pytest.mark.parametrize(
    "changes",
    [
        {"client_secret": None},
        {"client_id": ""},
        {"api_url": "http://api.test.example"},
        {"api_url": "https://user:test-secret@api.test.example"},
        {"api_url": "https://api.test.example?x=1"},
        {"token_url": "https://evil.example/oauth2/token"},
        {"token_url": "https://x.auth.us-east-1.amazoncognito.com/other"},
    ],
)
def test_invalid_credentials_are_refused(
    tmp_path: Path, credentials: dict, changes: dict
) -> None:
    with pytest.raises(CredentialsError) as raised:
        load_credentials(write(tmp_path, credentials, **changes))
    assert raised.value.reason == "invalid"
    assert "test-secret" not in str(raised.value)


def test_missing_credentials_file(tmp_path: Path) -> None:
    with pytest.raises(CredentialsError) as raised:
        load_credentials(tmp_path / "absent.json")
    assert raised.value.reason == "missing"


def test_settings_come_from_the_environment(tmp_path: Path) -> None:
    env = {
        "RESCUEBOX_SAFE_MATCH_MODE": "stub",
        "RESCUEBOX_SAFE_MATCH_DATA_DIR": str(tmp_path),
        "RESCUEBOX_SAFE_MATCH_PORT": "9000",
    }
    settings = Settings.from_env(env)
    assert (settings.mode, settings.host, settings.port) == ("stub", "127.0.0.1", 9000)
    assert settings.credentials_path == tmp_path / "credentials.json"
    with pytest.raises(SystemExit):
        Settings.from_env({"RESCUEBOX_SAFE_MATCH_MODE": "other"})
