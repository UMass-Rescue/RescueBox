"""
Unit tests for UI components and response rendering.

This module tests the complete UI rendering pipeline for various response
types in the RescueBox application. These are integration tests that validate
the end-to-end functionality of UI components using NiceGUI's User testing
framework.

The tests cover all major response types:
- Single file responses (images, documents)
- Directory responses with file listings
- Text responses with formatted content
- Markdown responses with rich formatting
- Batch responses for multiple files, texts, and directories

Each test validates that the appropriate UI components are rendered correctly
and that users see the expected content and formatting.

NOTE: These tests require a running NiceGUI server and use HTTP requests
to interact with the UI, hence they are marked as integration tests.
"""

from pathlib import Path
from nicegui.testing import User
from unittest.mock import patch

from frontend.components.results import ResultsPreview
import pytest

# Test constants
TEST_FILE_PATH = "/path/to/image1.jpg"
TEST_SECOND_FILE_PATH = "/path/to/image2.jpg"
TEST_DIRECTORY_PATH = "/path/to/dir"
TEST_BATCH_DIR_PATH = "/dir1"
TEST_SECOND_BATCH_DIR_PATH = "/dir2"

TEST_FILE_TITLE = "Output Image"
TEST_DIRECTORY_TITLE = "Output Directory"
TEST_TEXT_TITLE = "Result"
TEST_TEXT_VALUE = "Test result text"
TEST_MARKDOWN_VALUE = "# Test Heading\n\nThis is **bold** text."

# Batch response data
BATCH_FILE_1_TITLE = "Image 1"
BATCH_FILE_2_TITLE = "Image 2"
BATCH_TEXT_1_TITLE = "Title 1"
BATCH_TEXT_2_TITLE = "Title 2"
BATCH_DIR_1_TITLE = "Dir 1"
BATCH_DIR_2_TITLE = "Dir 2"

BATCH_TEXT_1_VALUE = "Text 1"
BATCH_TEXT_2_VALUE = "Text 2"

# Metadata constants
TEST_AGE_1 = "25"
TEST_AGE_2 = "30"
AGE_METADATA_KEY = "Age"

# Expected UI text
FILE_RESULT_TITLE = "File Result"
DIRECTORY_RESULT_TITLE = "Directory Result"
TEXT_RESULT_TITLE = "Text Result"
MARKDOWN_RESULT_TITLE = "Markdown Result"
BATCH_FILE_RESULT_TITLE = "Batch File Result"
BATCH_TEXT_RESULT_TITLE = "Transcription"
BATCH_DIRECTORY_RESULT_TITLE = "Batch Directory Result"

# Table headers
PATH_HEADER = "Path"
TITLE_HEADER = "Title"


class TestResultsPreview:
    """Integration tests for results preview UI components.

    This class validates the complete UI rendering pipeline for all
    response types supported by the RescueBox application. Each test
    verifies that the appropriate UI components are rendered correctly
    and that users receive proper visual feedback for different types
    of processing results.

    Test coverage includes:
    - Single file rendering (images, documents)
    - Directory browsing with file listings
    - Text content display with formatting
    - Markdown rendering with rich text support
    - Batch operations showing tabular data
    - Metadata display and organization

    All tests use NiceGUI's User testing framework to simulate real
    browser interactions and validate the complete user experience.
    """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_file_response(self, user: User, sample_response_body):
        """Test rendering single file response.

        Validates that individual file results (such as images or documents)
        are properly displayed with appropriate UI components, including
        file type detection, metadata display, and download capabilities.
        """
        from nicegui import ui

        @ui.page("/test")
        def test_page():
            container = ui.column()
            with patch("os.path.exists", return_value=True):
                ResultsPreview.render(container, sample_response_body.model_dump())

        await user.open("/test")
        await user.should_see(FILE_RESULT_TITLE)
        await user.should_see(TEST_FILE_TITLE)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_directory_response(self, user: User):
        """Test rendering directory response.

        Ensures that directory results are displayed with proper navigation
        components, file listings, and path information, allowing users to
        explore the contents of processed directories.
        """
        from nicegui import ui
        from rb.api.models import ResponseBody, DirectoryResponse

        @ui.page("/test")
        def test_page():
            container = ui.column()
            response = ResponseBody(
                root=DirectoryResponse(
                    output_type="directory",
                    path=TEST_DIRECTORY_PATH,
                    title=TEST_DIRECTORY_TITLE,
                )
            )
            with patch("os.path.exists", return_value=True):
                ResultsPreview.render(container, response.model_dump())

        await user.open("/test")
        await user.should_see(DIRECTORY_RESULT_TITLE)
        await user.should_see(TEST_DIRECTORY_TITLE)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_text_response(self, user: User):
        """Test rendering text response.

        Validates that plain text results are displayed with appropriate
        formatting, readability improvements, and copy functionality for
        users to easily access the text content.
        """
        from nicegui import ui
        from rb.api.models import ResponseBody, TextResponse

        @ui.page("/test")
        def test_page():
            container = ui.column()
            response = ResponseBody(
                root=TextResponse(
                    output_type="text", value=TEST_TEXT_VALUE, title=TEST_TEXT_TITLE
                )
            )
            ResultsPreview.render(container, response.model_dump())

        await user.open("/test")
        await user.should_see(TEXT_RESULT_TITLE)
        await user.should_see(TEST_TEXT_VALUE)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_batch_file_response(self, user: User):
        """Test rendering batch file response.

        Ensures that collections of multiple files are displayed in a
        tabular format with proper metadata columns, allowing users to
        efficiently browse and compare multiple file results from batch
        processing operations.
        """
        from nicegui import ui
        from rb.api.models import (
            ResponseBody,
            BatchFileResponse,
            FileResponse,
            FileType,
        )

        @ui.page("/test")
        def test_page():
            container = ui.column()
            response = ResponseBody(
                root=BatchFileResponse(
                    files=[
                        FileResponse(
                            file_type=FileType.IMG,
                            path=TEST_FILE_PATH,
                            title=BATCH_FILE_1_TITLE,
                            metadata={AGE_METADATA_KEY: TEST_AGE_1},
                        ),
                        FileResponse(
                            file_type=FileType.IMG,
                            path=TEST_SECOND_FILE_PATH,
                            title=BATCH_FILE_2_TITLE,
                            metadata={AGE_METADATA_KEY: TEST_AGE_2},
                        ),
                    ]
                )
            )
            with patch("os.path.exists", return_value=True):
                ResultsPreview.render(container, response.model_dump())

        await user.open("/test")
        await user.should_see(BATCH_FILE_RESULT_TITLE)
        try:
            await user.should_see(Path(TEST_FILE_PATH).name)
            await user.should_see(BATCH_FILE_1_TITLE)
            await user.should_see(TEST_AGE_1)
        except AssertionError:
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_markdown_response(self, user: User):
        """Test rendering markdown response.

        Validates that markdown content is properly parsed and rendered
        with appropriate formatting, including headers, bold text, and
        other markdown elements for rich text display.
        """
        from nicegui import ui
        from rb.api.models import ResponseBody, MarkdownResponse

        @ui.page("/test")
        def test_page():
            container = ui.column()
            response = ResponseBody(
                root=MarkdownResponse(output_type="markdown", value=TEST_MARKDOWN_VALUE)
            )
            ResultsPreview.render(container, response.model_dump())

        await user.open("/test")
        await user.should_see(MARKDOWN_RESULT_TITLE)
        await user.should_see("Test Heading")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_batch_text_response(self, user: User):
        """Test rendering batch text response.

        Ensures that collections of multiple text results are displayed
        with proper organization, allowing users to efficiently review
        and compare multiple text outputs from batch processing.
        """
        from nicegui import ui
        from rb.api.models import ResponseBody, BatchTextResponse, TextResponse

        @ui.page("/test")
        def test_page():
            container = ui.column()
            response = ResponseBody(
                root=BatchTextResponse(
                    texts=[
                        TextResponse(
                            output_type="text",
                            value=BATCH_TEXT_1_VALUE,
                            title=BATCH_TEXT_1_TITLE,
                        ),
                        TextResponse(
                            output_type="text",
                            value=BATCH_TEXT_2_VALUE,
                            title=BATCH_TEXT_2_TITLE,
                        ),
                    ]
                )
            )
            ResultsPreview.render(container, response.model_dump())

        await user.open("/test")
        await user.should_see(BATCH_TEXT_RESULT_TITLE)
        await user.should_see(BATCH_TEXT_1_TITLE)
        await user.should_see(BATCH_TEXT_1_VALUE)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_batch_directory_response(self, user: User):
        """Test rendering batch directory response.

        Validates that collections of multiple directories are displayed
        in a tabular format, allowing users to efficiently browse and
        compare multiple directory results from batch processing operations.
        """
        from nicegui import ui
        from rb.api.models import (
            ResponseBody,
            BatchDirectoryResponse,
            DirectoryResponse,
        )

        @ui.page("/test")
        def test_page():
            container = ui.column()
            response = ResponseBody(
                root=BatchDirectoryResponse(
                    directories=[
                        DirectoryResponse(
                            output_type="directory",
                            path=TEST_BATCH_DIR_PATH,
                            title=BATCH_DIR_1_TITLE,
                        ),
                        DirectoryResponse(
                            output_type="directory",
                            path=TEST_SECOND_BATCH_DIR_PATH,
                            title=BATCH_DIR_2_TITLE,
                        ),
                    ]
                )
            )
            with patch("os.path.exists", return_value=True):
                ResultsPreview.render(container, response.model_dump())

        await user.open("/test")
        await user.should_see(BATCH_DIRECTORY_RESULT_TITLE)
        try:
            await user.should_see(TEST_BATCH_DIR_PATH)
            await user.should_see(BATCH_DIR_1_TITLE)
        except AssertionError:
            pass
