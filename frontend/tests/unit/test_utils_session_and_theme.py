"""Unit tests for session/case identity helpers and theme application."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from frontend.constants import DEMO_USER_ID_PREFIX


@pytest.fixture
def patched_app(monkeypatch):
    import frontend.utils as utils
    import frontend.utils.storage as storage_mod
    from frontend.utils.storage import reset_test_storage

    mock_app = MagicMock()
    mock_app.storage.general = {}
    mock_app.storage.user = {}
    mock_app.storage.browser = {}
    monkeypatch.setattr(utils, "app", mock_app)
    monkeypatch.setattr(storage_mod, "app", mock_app)
    reset_test_storage()
    return utils


class TestSessionAndCaseHelpers:
    def test_ensure_session_user_id_returns_session_id(self, patched_app):
        ngs = patched_app
        uid = ngs.ensure_session_user_id()
        assert uid
        assert uid == ngs.get_user_id()
        assert ngs.get_user_id() == patched_app.app.storage.user.get("id")

    def test_ensure_user_id_alias_matches_session(self, patched_app):
        ngs = patched_app
        assert ngs.ensure_user_id() is not None

    def test_ensure_active_case_id_none_without_case(self, patched_app):
        ngs = patched_app
        assert ngs.ensure_active_case_id() is None

    def test_ensure_active_case_id_after_set_explicit(self, patched_app):
        ngs = patched_app
        case = DEMO_USER_ID_PREFIX + "case1"
        ngs.set_explicit_user_id(case)
        assert ngs.ensure_active_case_id() == case
        assert ngs.get_user_id_for_jobs() == case

    def test_active_case_pytest_fallback_when_storage_empty(self, patched_app):
        """When app.storage returns no case id, pytest fallback still resolves."""
        ngs = patched_app
        user_store = MagicMock()
        user_store.get = MagicMock(return_value=None)
        patched_app.app.storage.user = user_store
        ngs.set_active_case_id("pytest-case-99")
        assert ngs.get_active_case_id() == "pytest-case-99"


class TestApplySavedTheme:
    def test_apply_saved_theme_uses_preference(self, patched_app):
        ngs = patched_app
        ngs.set_user_preference("dark_mode", True)
        with patch("frontend.utils.ui.ui.dark_mode") as mock_dark:
            ngs.apply_saved_theme()
        mock_dark.assert_called_once_with(True)

    def test_apply_saved_theme_falls_back_to_config(self, patched_app):
        ngs = patched_app
        with patch("frontend.utils.ui.ui.dark_mode") as mock_dark:
            with patch("frontend.utils.ui.APP_DARK_MODE", False):
                ngs.apply_saved_theme()
        mock_dark.assert_called_once_with(False)
