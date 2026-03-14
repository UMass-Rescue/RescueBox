"""
Unit tests for results utilities error handling.

This module tests the robustness of file and folder opening operations
across different platforms (Windows, macOS, Linux). It validates that
various error conditions are handled gracefully, including:

- Empty or invalid paths
- Nonexistent files/folders
- Permission errors
- Platform-specific subprocess failures
- Generic exceptions during file operations

The tests ensure users receive appropriate error messages when file
system operations fail, maintaining a good user experience even when
external operations encounter problems.

Platform-specific testing covers:
- Windows: Uses os.startfile() with error handling
- macOS: Uses subprocess.run() with 'open' command
- Linux: Uses subprocess.run() with 'xdg-open' command
"""

import pytest
import os
import subprocess
import platform
from unittest.mock import patch, MagicMock

from frontend.components.results.results_utils import open_file, open_folder

# Test constants
EMPTY_PATH = ""
NONEXISTENT_FILE_PATH = "/nonexistent/file.txt"
NONEXISTENT_FOLDER_PATH = "/nonexistent/folder"
TEST_FILE_PATH = "/tmp/test.txt"
TEST_FOLDER_PATH = "/tmp"
DIRECTORY_AS_FILE_PATH = "/tmp"  # Directory used as file path
FILE_AS_FOLDER_PATH = "/tmp/test.txt"  # File used as folder path

# Error message patterns
ERROR_OPENING_FILE_PREFIX = "Error opening file"
INVALID_FOLDER_PATH_MSG = "Invalid folder path"
FOLDER_NOT_FOUND_MSG = "Folder not found"
PATH_IS_NOT_FOLDER_MSG = "Path is not a folder"
FAILED_TO_OPEN_FOLDER_MSG = "Failed to open folder"

# Platform constants
WINDOWS_PLATFORM = 'Windows'
DARWIN_PLATFORM = 'Darwin'
LINUX_PLATFORM = 'Linux'


class TestResultsUtilsErrorHandling:
    """Tests for results utilities error handling and edge cases.

    This class validates the robustness of file and folder opening operations
    by testing various error conditions that can occur in real-world usage:

    File opening errors:
    - Empty or invalid file paths
    - Nonexistent files
    - Permission denied errors
    - Platform-specific subprocess failures

    Folder opening errors:
    - Empty or invalid folder paths
    - Nonexistent directories
    - Path pointing to a file instead of directory
    - Permission and subprocess errors

    All tests ensure appropriate error messages are displayed to users
    when file system operations fail.
    """
    
    def test_open_file_empty_path(self):
        """Test handling of empty file path.

        Validates that empty or invalid file paths are handled gracefully
        with appropriate error messages, preventing crashes when users
        provide malformed input.
        """
        with patch('nicegui.ui.notify') as mock_notify:
            # Mock platform-specific file opening to simulate empty path error
            current_platform = platform.system()

            if current_platform == WINDOWS_PLATFORM:
                with patch('frontend.components.results.results_utils.os.startfile',
                          side_effect=OSError(2, "The system cannot find the file specified", "")):
                    open_file(EMPTY_PATH)
            elif current_platform == DARWIN_PLATFORM:
                with patch('frontend.components.results.results_utils.subprocess.run',
                          side_effect=FileNotFoundError("No such file or directory")):
                    open_file(EMPTY_PATH)
            else:  # Linux and other Unix-like systems
                with patch('frontend.components.results.results_utils.subprocess.run',
                          side_effect=FileNotFoundError("No such file or directory")):
                    open_file(EMPTY_PATH)

            # Verify error notification was displayed
            mock_notify.assert_called_once()
            call_args_str = str(mock_notify.call_args)
            assert ERROR_OPENING_FILE_PREFIX in call_args_str
    
    def test_open_file_nonexistent_file(self):
        """Test handling of nonexistent file.

        Ensures that attempts to open files that don't exist on the
        filesystem are handled gracefully with informative error
        messages across all supported platforms.
        """
        with patch('nicegui.ui.notify') as mock_notify:
            current_platform = platform.system()

            # Mock platform-specific file opening to simulate file not found
            if current_platform == WINDOWS_PLATFORM:
                with patch('frontend.components.results.results_utils.os.startfile',
                          side_effect=FileNotFoundError(2, "The system cannot find the file specified", NONEXISTENT_FILE_PATH)):
                    open_file(NONEXISTENT_FILE_PATH)
            elif current_platform == DARWIN_PLATFORM:
                with patch('frontend.components.results.results_utils.subprocess.run',
                          side_effect=FileNotFoundError("No such file or directory")):
                    open_file(NONEXISTENT_FILE_PATH)
            else:  # Linux and other Unix-like systems
                with patch('frontend.components.results.results_utils.subprocess.run',
                          side_effect=FileNotFoundError("No such file or directory")):
                    open_file(NONEXISTENT_FILE_PATH)

            # Verify error notification was displayed with appropriate message
            mock_notify.assert_called_once()
            call_args_str = str(mock_notify.call_args)
            assert ERROR_OPENING_FILE_PREFIX in call_args_str
            # Check for platform-appropriate error messages
            assert ("cannot find" in call_args_str or
                   "File not found" in call_args_str or
                   "No such file" in call_args_str)
    
    def test_open_file_path_is_directory(self):
        """Test handling of path that is a directory, not a file"""
        with patch('nicegui.ui.notify') as mock_notify:
            # Don't mock - let it fail naturally when trying to open a directory as a file
            # On Windows, /tmp doesn't exist, so it will fail with file not found error
            open_file("/tmp")
            mock_notify.assert_called_once()
            # Error message includes "Error opening file: " prefix
            call_args_str = str(mock_notify.call_args)
            assert "Error opening file" in call_args_str
    
    @patch('platform.system')
    def test_open_file_file_not_found_error_windows(self, mock_system):
        """Test handling of FileNotFoundError on Windows"""
        mock_system.return_value = 'Windows'
        with patch('nicegui.ui.notify') as mock_notify:
            with patch('frontend.components.results.results_utils.os.path.exists', return_value=True):
                with patch('frontend.components.results.results_utils.os.path.isfile', return_value=True):
                    with patch('frontend.components.results.results_utils.os.startfile', side_effect=FileNotFoundError("File not found")):
                        open_file("/tmp/test.txt")
                        mock_notify.assert_called_once()
                        # Error message format: "Error opening file: File not found"
                        call_args_str = str(mock_notify.call_args)
                        assert "Error opening file" in call_args_str
                        assert "File not found" in call_args_str
    
    @patch('platform.system')
    def test_open_file_permission_error_windows(self, mock_system):
        """Test handling of PermissionError on Windows"""
        mock_system.return_value = 'Windows'
        with patch('nicegui.ui.notify') as mock_notify:
            with patch('frontend.components.results.results_utils.os.path.exists', return_value=True):
                with patch('frontend.components.results.results_utils.os.path.isfile', return_value=True):
                    with patch('frontend.components.results.results_utils.os.startfile', side_effect=PermissionError("Permission denied")):
                        open_file("/tmp/test.txt")
                        mock_notify.assert_called_once()
                        # Error message format: "Error opening file: Permission denied"
                        call_args_str = str(mock_notify.call_args)
                        assert "Error opening file" in call_args_str
                        assert "Permission denied" in call_args_str
    
    @patch('platform.system')
    def test_open_file_subprocess_error_macos(self, mock_system):
        """Test handling of subprocess error on macOS"""
        mock_system.return_value = 'Darwin'
        with patch('nicegui.ui.notify') as mock_notify:
            with patch('frontend.components.results.results_utils.os.path.exists', return_value=True):
                with patch('frontend.components.results.results_utils.os.path.isfile', return_value=True):
                    with patch('frontend.components.results.results_utils.subprocess.run', side_effect=subprocess.CalledProcessError(1, "open")):
                        open_file("/tmp/test.txt")
                        mock_notify.assert_called_once()
                        # Error message includes "Error opening file: " prefix
                        call_args_str = str(mock_notify.call_args)
                        assert "Error opening file" in call_args_str
    
    @patch('platform.system')
    def test_open_file_generic_exception(self, mock_system):
        """Test handling of generic exception"""
        mock_system.return_value = 'Linux'
        with patch('nicegui.ui.notify') as mock_notify:
            with patch('frontend.components.results.results_utils.os.path.exists', return_value=True):
                with patch('frontend.components.results.results_utils.os.path.isfile', return_value=True):
                    with patch('frontend.components.results.results_utils.subprocess.run', side_effect=Exception("Unexpected error")):
                        open_file("/tmp/test.txt")
                        mock_notify.assert_called_once()
                        assert "Error opening file" in str(mock_notify.call_args)
    
    def test_open_folder_empty_path(self):
        """Test handling of empty folder path.

        Validates that empty folder paths are rejected with clear
        error messages, preventing attempts to open invalid directories.
        """
        with patch('nicegui.ui.notify') as mock_notify:
            open_folder(EMPTY_PATH)
            mock_notify.assert_called_once()
            assert INVALID_FOLDER_PATH_MSG in str(mock_notify.call_args)

    def test_open_folder_nonexistent_folder(self):
        """Test handling of nonexistent folder.

        Ensures that attempts to open directories that don't exist
        are handled gracefully with appropriate user feedback.
        """
        with patch('nicegui.ui.notify') as mock_notify:
            with patch('frontend.components.results.results_utils.os.path.exists', return_value=False):
                open_folder(NONEXISTENT_FOLDER_PATH)
                mock_notify.assert_called_once()
                assert FOLDER_NOT_FOUND_MSG in str(mock_notify.call_args)
    
    def test_open_folder_path_is_file(self):
        """Test handling of path that points to a file instead of directory.

        Validates that paths pointing to files (rather than directories)
        are properly detected and rejected when attempting folder operations,
        with clear error messages explaining the issue.
        """
        with patch('nicegui.ui.notify') as mock_notify:
            with patch('frontend.components.results.results_utils.os.path.exists', return_value=True):
                with patch('frontend.components.results.results_utils.os.path.isdir', return_value=False):
                    open_folder(FILE_AS_FOLDER_PATH)
                    mock_notify.assert_called_once()
                    assert PATH_IS_NOT_FOLDER_MSG in str(mock_notify.call_args)
    
    @patch('platform.system')
    def test_open_folder_file_not_found_error(self, mock_system):
        """Test handling of FileNotFoundError when opening folder"""
        mock_system.return_value = 'Windows'
        with patch('nicegui.ui.notify') as mock_notify:
            with patch('frontend.components.results.results_utils.os.path.exists', return_value=True):
                with patch('frontend.components.results.results_utils.os.path.isdir', return_value=True):
                    with patch('frontend.components.results.results_utils.os.startfile', side_effect=FileNotFoundError("Folder not found")):
                        open_folder("/tmp")
                        mock_notify.assert_called_once()
                        assert "Folder not found" in str(mock_notify.call_args)
    
    @patch('platform.system')
    def test_open_folder_permission_error(self, mock_system):
        """Test handling of PermissionError when opening folder"""
        mock_system.return_value = 'Windows'
        with patch('nicegui.ui.notify') as mock_notify:
            with patch('frontend.components.results.results_utils.os.path.exists', return_value=True):
                with patch('frontend.components.results.results_utils.os.path.isdir', return_value=True):
                    with patch('frontend.components.results.results_utils.os.startfile', side_effect=PermissionError("Permission denied")):
                        open_folder("/tmp")
                        mock_notify.assert_called_once()
                        assert "Permission denied" in str(mock_notify.call_args)
    
    @patch('platform.system')
    def test_open_folder_subprocess_error(self, mock_system):
        """Test handling of subprocess error when opening folder"""
        mock_system.return_value = 'Linux'
        with patch('nicegui.ui.notify') as mock_notify:
            with patch('frontend.components.results.results_utils.os.path.exists', return_value=True):
                with patch('frontend.components.results.results_utils.os.path.isdir', return_value=True):
                    with patch('frontend.components.results.results_utils.subprocess.run', side_effect=subprocess.CalledProcessError(1, "xdg-open")):
                        open_folder("/tmp")
                        mock_notify.assert_called_once()
                        assert "Failed to open folder" in str(mock_notify.call_args)

