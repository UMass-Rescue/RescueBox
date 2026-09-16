"""Unit tests for frontend.config data and log paths."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import patch


def _reload_config():
    if "frontend.config" in sys.modules:
        return importlib.reload(sys.modules["frontend.config"])
    return importlib.import_module("frontend.config")


def test_linux_log_file_under_rescuebox_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    with patch("platform.system", return_value="Linux"), patch.object(Path, "mkdir"):
        mod = _reload_config()
    assert mod.LOG_FILE == home / ".rescuebox" / "logs" / "frontend.log"
    assert mod.DATA_DIR == home / ".rescuebox" / "data"


def test_windows_data_and_log_under_local_appdata(tmp_path, monkeypatch):
    local = tmp_path / "AppData" / "Local"
    local.mkdir(parents=True)
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    with patch("platform.system", return_value="Windows"), patch.object(Path, "mkdir"):
        mod = _reload_config()
    assert mod.DATA_DIR == local / "RescueBox" / "data"
    assert mod.LOG_FILE == local / "RescueBox" / "logs" / "frontend.log"


def test_app_show_browser_respects_false_env(monkeypatch):
    monkeypatch.delenv("RESCUEBOX_SHOW_BROWSER", raising=False)
    with patch.object(Path, "mkdir"):
        monkeypatch.setenv("RESCUEBOX_SHOW_BROWSER", "false")
        mod = _reload_config()
    assert mod.APP_SHOW_BROWSER is False


def test_app_show_browser_true_when_env_true(monkeypatch):
    with patch.object(Path, "mkdir"):
        monkeypatch.setenv("RESCUEBOX_SHOW_BROWSER", "true")
        mod = _reload_config()
    assert mod.APP_SHOW_BROWSER is True


def test_demo_files_browse_root_uses_src_tauri_demo_when_repo_demo_missing(
    monkeypatch,
):
    monkeypatch.delenv("RESCUEBOX_DEMO_FILES_DIR", raising=False)
    monkeypatch.delenv("RESCUEBOX_HOME", raising=False)
    with patch.object(Path, "mkdir"):
        mod = _reload_config()
    expected = mod._REPO_ROOT / "src-tauri" / "demo"
    assert mod.DEMO_FILES_BROWSE_ROOT == expected


def test_backend_log_file_macos_matches_frontend_default(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("RESCUEBOX_API_LOG_FILE", raising=False)
    with patch("platform.system", return_value="Darwin"), patch.object(Path, "mkdir"):
        mod = _reload_config()
    from rb.api import logging_setup

    with patch.object(logging_setup.platform, "system", return_value="Darwin"):
        backend_path = logging_setup.backend_log_file_path()

    assert backend_path == mod.BACKEND_LOG_FILE


def test_demo_files_browse_root_respects_explicit_env(tmp_path, monkeypatch):
    demo = tmp_path / "my-demo"
    demo.mkdir()
    monkeypatch.setenv("RESCUEBOX_DEMO_FILES_DIR", str(demo))
    with patch.object(Path, "mkdir"):
        mod = _reload_config()
    assert mod.DEMO_FILES_BROWSE_ROOT == demo


def test_app_show_browser_false_when_frozen_without_env(monkeypatch):
    monkeypatch.delenv("RESCUEBOX_SHOW_BROWSER", raising=False)
    with patch.object(Path, "mkdir"), patch.object(sys, "frozen", True, create=True):
        mod = _reload_config()
    assert mod.APP_SHOW_BROWSER is False
