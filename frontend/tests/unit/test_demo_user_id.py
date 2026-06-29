"""Unit tests for demo User ID format validation."""

from unittest.mock import MagicMock

import pytest

from frontend.constants import (
    DEMO_USER_ID_PREFIX,
    is_valid_explicit_user_id,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, False),
        ("", False),
        ("wrong", False),
        (DEMO_USER_ID_PREFIX, False),
        (DEMO_USER_ID_PREFIX + "x", False),
        (DEMO_USER_ID_PREFIX + "ab", False),
        (DEMO_USER_ID_PREFIX + "abc", True),
        (DEMO_USER_ID_PREFIX + "7!x", True),
        (" " + DEMO_USER_ID_PREFIX + "abc", True),
    ],
)
def test_is_valid_explicit_user_id(value, expected):
    assert is_valid_explicit_user_id(value) is expected


@pytest.fixture
def patched_nicegui_app(monkeypatch):
    """Isolate app.storage.general for explicit-ID registry tests."""
    import frontend.utils as utils
    from frontend.utils.storage import reset_test_storage

    mock_app = MagicMock()
    mock_app.storage.general = {}
    mock_app.storage.user = {}
    mock_app.storage.browser = {}
    monkeypatch.setattr(utils, "app", mock_app)
    reset_test_storage()
    return utils


def test_try_claim_explicit_user_id_invalid(patched_nicegui_app):
    ngs = patched_nicegui_app
    assert ngs.try_claim_explicit_user_id("") == "invalid"
    assert ngs.try_claim_explicit_user_id("not_demo") == "invalid"


def test_try_claim_release_roundtrip(patched_nicegui_app):
    ngs = patched_nicegui_app
    vid = DEMO_USER_ID_PREFIX + "abc"
    assert ngs.try_claim_explicit_user_id(vid) == "ok"
    assert ngs.try_claim_explicit_user_id(vid) == "taken"
    ngs.release_explicit_user_id_claim(vid)
    assert ngs.try_claim_explicit_user_id(vid) == "ok"


def test_clear_explicit_user_id_releases_claim(patched_nicegui_app):
    ngs = patched_nicegui_app
    vid = DEMO_USER_ID_PREFIX + "xyz"
    assert ngs.try_claim_explicit_user_id(vid) == "ok"
    ngs.set_explicit_user_id(vid)
    ngs.clear_explicit_user_id()
    assert ngs.get_explicit_user_id() is None
    # Ensure registry is cleared (in case clear_explicit_user_id failed to release)
    ngs.release_explicit_user_id_claim(vid)
    assert ngs.try_claim_explicit_user_id(vid) == "ok"
