"""
Unit tests for results utilities error handling.

open_file serves files via in-app routes and ui.navigate; open_folder uses
platform-specific explorers. Tests patch the module under test (results_utils.ui).
"""

import pytest
import subprocess
from unittest.mock import patch

from frontend.components import results as results_utils
from frontend.components.results import open_file, open_folder

EMPTY_PATH = ""
NONEXISTENT_FOLDER_PATH = "/nonexistent/folder"
INVALID_FOLDER_PATH_MSG = "Invalid folder path"
FOLDER_NOT_FOUND_MSG = "Folder not found"
PATH_IS_NOT_FOLDER_MSG = "Path is not a folder"
FILE_AS_FOLDER_PATH = "/tmp/test.txt"


class TestResultsUtilsErrorHandling:
    def test_open_file_navigate_failure_notifies(self):
        with patch.object(results_utils.ui, "navigate") as mock_nav:
            mock_nav.to.side_effect = RuntimeError("no client")
            with patch.object(results_utils.ui, "notify") as mock_notify:
                open_file("/tmp/some_file.txt")
        mock_notify.assert_called_once()
        assert "Error opening file" in str(mock_notify.call_args)

    def test_open_file_reuses_route_navigate_failure_notifies(self):
        """Second open for same path hits existing-token branch; navigate can still fail."""
        results_utils._SERVED_FILES.clear()
        token = "deadbeef"
        results_utils._SERVED_FILES[token] = {"path": "/tmp/x.txt", "created": 0}
        with patch.object(results_utils.ui, "navigate") as mock_nav:
            mock_nav.to.side_effect = [None, RuntimeError("fail")]
            with patch.object(results_utils.ui, "notify") as mock_notify:
                open_file("/tmp/x.txt")
                open_file("/tmp/x.txt")
        assert mock_notify.called
        assert "Error opening file" in str(mock_notify.call_args)
        results_utils._SERVED_FILES.clear()

    def test_open_folder_empty_path(self):
        with patch.object(results_utils.ui, "notify") as mock_notify:
            open_folder(EMPTY_PATH)
        mock_notify.assert_called_once()
        assert INVALID_FOLDER_PATH_MSG in str(mock_notify.call_args)

    def test_open_folder_nonexistent_folder(self):
        with patch.object(results_utils.ui, "notify") as mock_notify:
            with patch.object(results_utils.os.path, "exists", return_value=False):
                open_folder(NONEXISTENT_FOLDER_PATH)
        mock_notify.assert_called_once()
        assert FOLDER_NOT_FOUND_MSG in str(mock_notify.call_args)

    def test_open_folder_path_is_file(self):
        with patch.object(results_utils.ui, "notify") as mock_notify:
            with patch.object(results_utils.os.path, "exists", return_value=True):
                with patch.object(results_utils.os.path, "isdir", return_value=False):
                    open_folder(FILE_AS_FOLDER_PATH)
        mock_notify.assert_called_once()
        assert PATH_IS_NOT_FOLDER_MSG in str(mock_notify.call_args)

    @patch.object(results_utils.platform, "system", return_value="Windows")
    def test_open_folder_file_not_found_error_windows(self, _mock_sys):
        with patch.object(results_utils.ui, "notify") as mock_notify:
            with patch.object(results_utils.os.path, "exists", return_value=True):
                with patch.object(results_utils.os.path, "isdir", return_value=True):
                    with patch.object(
                        results_utils.os,
                        "startfile",
                        create=True,
                        side_effect=FileNotFoundError("Folder not found"),
                    ):
                        open_folder("/tmp")
        mock_notify.assert_called_once()
        assert "Folder not found" in str(mock_notify.call_args)

    @patch.object(results_utils.platform, "system", return_value="Windows")
    def test_open_folder_permission_error_windows(self, _mock_sys):
        with patch.object(results_utils.ui, "notify") as mock_notify:
            with patch.object(results_utils.os.path, "exists", return_value=True):
                with patch.object(results_utils.os.path, "isdir", return_value=True):
                    with patch.object(
                        results_utils.os,
                        "startfile",
                        create=True,
                        side_effect=PermissionError("Permission denied"),
                    ):
                        open_folder("/tmp")
        mock_notify.assert_called_once()
        assert "Permission denied" in str(mock_notify.call_args)

    @patch.object(results_utils.platform, "system", return_value="Linux")
    def test_open_folder_subprocess_error(self, _mock_sys):
        with patch.object(results_utils.ui, "notify") as mock_notify:
            with patch.object(results_utils.os.path, "exists", return_value=True):
                with patch.object(results_utils.os.path, "isdir", return_value=True):
                    with patch.object(
                        results_utils.subprocess,
                        "run",
                        side_effect=subprocess.CalledProcessError(1, "xdg-open"),
                    ):
                        open_folder("/tmp")
        mock_notify.assert_called_once()
        assert "Failed to open folder" in str(mock_notify.call_args)
