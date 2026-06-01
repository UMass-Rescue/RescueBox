"""
Unit tests for file renderers error handling functionality.

This module tests the robustness of file rendering components by validating
that various error conditions are handled gracefully, including missing files,
corrupted data, and unexpected exceptions during the rendering process.

The tests ensure that users receive appropriate error messages and that
the application remains stable even when file operations fail.
"""

from unittest.mock import MagicMock, Mock, patch

from rb.api.models import FileResponse, FileType

from frontend.components.results import render_file

# Test constants
TEST_FILE_TITLE = "Test File"
TEST_IMAGE_TITLE = "Test Image"
EMPTY_PATH = ""
NONEXISTENT_IMAGE_PATH = "/nonexistent/image.jpg"
VALID_IMAGE_PATH = "/tmp/test.jpg"
VALID_TEXT_PATH = "/tmp/test.txt"
IMAGE_LOAD_ERROR_MSG = "Image load error"


class TestFileRenderersErrorHandling:
    """Tests for file renderers error handling and edge cases.

    This class validates that file rendering components handle various
    error conditions gracefully, ensuring users get appropriate feedback
    and the application remains stable when file operations fail.

    Error scenarios tested:
    - Empty or invalid file paths
    - Missing or inaccessible files
    - File loading and processing errors
    - Unexpected exceptions during rendering
    """

    def _create_mock_container(self):
        """Create a mock container that supports context manager protocol."""
        container = MagicMock()
        container.__enter__ = Mock(return_value=container)
        container.__exit__ = Mock(return_value=False)
        return container

    def test_render_file_empty_path(self):
        """Test handling of file response with empty path.

        Validates that the renderer properly handles FileResponse objects
        with empty or missing file paths, displaying appropriate error
        messages instead of crashing.
        """
        response = FileResponse(
            file_type=FileType.TEXT,
            path=EMPTY_PATH,
            title=TEST_FILE_TITLE
        )

        # Create mock container that supports context manager protocol
        container = MagicMock()
        container.__enter__ = Mock(return_value=container)
        container.__exit__ = Mock(return_value=False)

        with patch('frontend.components.results.ui') as mock_ui:
            mock_label = MagicMock()
            mock_ui.label = Mock(return_value=mock_label)

            render_file(container, response)

            # Verify that an error label was added to the container
            assert mock_ui.label.called
    
    def test_render_file_nonexistent_image(self):
        """Test handling of nonexistent image file.

        Ensures that when an image file doesn't exist on disk, the renderer
        detects this condition and displays an appropriate error message
        instead of attempting to load and display a missing file.
        """
        response = FileResponse(
            file_type=FileType.IMG,
            path=NONEXISTENT_IMAGE_PATH,
            title=TEST_IMAGE_TITLE
        )

        container = self._create_mock_container()

        with patch('frontend.components.results.os.path.exists', return_value=False):
            with patch('frontend.components.results.ui') as mock_ui:
                render_file(container, response)

                # Verify error message is displayed
                mock_ui.label.assert_called()
                # Check that appropriate error text is shown
                call_args_list = [str(call) for call in mock_ui.label.call_args_list]
                assert any("not found" in str(call) or "Error" in str(call) for call in call_args_list)
    
    def test_render_file_image_load_error(self):
        """Test handling of error loading image file.

        Validates that when image loading fails due to file corruption,
        permission issues, or other IO problems, the renderer gracefully
        handles the error and displays an appropriate message to the user.
        """
        response = FileResponse(
            file_type=FileType.IMG,
            path=VALID_IMAGE_PATH,
            title=TEST_IMAGE_TITLE
        )

        container = self._create_mock_container()

        with patch('frontend.components.results.os.path.exists', return_value=True):
            with patch('frontend.components.results.ui') as mock_ui:
                # Simulate image loading failure
                mock_ui.image.side_effect = Exception(IMAGE_LOAD_ERROR_MSG)

                render_file(container, response)

                # Verify error message is displayed
                mock_ui.label.assert_called()
                # Check that appropriate error content is shown
                call_args_list = [str(call) for call in mock_ui.label.call_args_list]
                assert any("Error loading image" in str(call) or "error" in str(call).lower() for call in call_args_list)
    
    def test_render_file_generic_exception(self):
        """Test handling of generic exception during file rendering.

        Ensures that unexpected exceptions during the rendering process
        are caught and handled gracefully, with appropriate error feedback
        displayed to the user instead of crashing the application.
        """
        response = FileResponse(
            file_type=FileType.TEXT,
            path=VALID_TEXT_PATH,
            title=TEST_FILE_TITLE
        )

        # Create a container that raises exceptions to simulate rendering errors
        class ExceptionRaisingContainer:
            """Mock container that raises exceptions during rendering."""
            def __init__(self):
                self.enter_count = 0

            def __enter__(self):
                self.enter_count += 1
                if self.enter_count == 1:
                    # First call (in main try block) raises exception
                    raise Exception("Rendering error")
                # Second call (in except block) succeeds
                return self

            def __exit__(self, *args):
                return None

        container = ExceptionRaisingContainer()

        with patch('frontend.components.results.ui') as mock_ui:
            # Mock all UI components to avoid actual UI calls
            mock_label = MagicMock()
            mock_ui.label = Mock(return_value=mock_label)
            mock_ui.card = Mock(return_value=MagicMock())
            mock_ui.column = Mock(return_value=MagicMock())
            mock_ui.row = Mock(return_value=MagicMock())
            mock_ui.button = Mock(return_value=MagicMock())

            render_file(container, response)

            # Verify exception was caught and error handling occurred
            assert container.enter_count >= 1  # Container was accessed
            assert mock_ui.label.called  # Error message was displayed

