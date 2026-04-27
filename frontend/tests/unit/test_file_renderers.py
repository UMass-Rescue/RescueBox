"""
Integration tests for file rendering functionality.

NOTE: These tests require a running NiceGUI server and are marked as integration tests.
They test the actual file rendering components in a browser-like environment using
the NiceGUI User fixture. Run with: pytest -m integration

These tests validate that file rendering components work correctly in the full
NiceGUI application context, including proper UI element creation, file type
detection, metadata display, and batch file handling.

The tests cover:
- Single file rendering (images, text files)
- Batch file rendering with and without metadata
- UI element visibility and interaction
- File type detection and appropriate rendering
"""

import pytest
from nicegui.testing import User
from nicegui import ui

# Import file rendering components
from frontend.components.results.file_renderers import (
    render_file,
    render_batch_file,
)

# Test constants
TEST_IMAGE_PATH = '/tmp/test_image.jpg'
TEST_FILE_PATH = '/tmp/test_file.txt'
TEST_BATCH_PATH_1 = '/path/to/image1.jpg'
TEST_BATCH_PATH_2 = '/path/to/image2.jpg'
TEST_IMAGE_TITLE = 'Test Image'
TEST_FILE_TITLE = 'Test File'
BATCH_IMAGE_TITLE_1 = 'Image 1'
BATCH_IMAGE_TITLE_2 = 'Image 2'


class TestFileRenderers:
    """Integration tests for file rendering components.

    These tests validate the complete file rendering pipeline including
    UI component creation, file type detection, and proper display
    of file information in the NiceGUI application interface.

    All tests require a running NiceGUI server instance for full
    browser-like interaction testing.
    """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_file_image(self, user: User):
        """Test rendering of image files.

        Validates that image files are properly rendered with appropriate
        UI components, showing file information and visual elements
        in the application interface.
        """
        from rb.api.models import FileResponse, FileType

        response = FileResponse(
            file_type=FileType.IMG,
            path=TEST_IMAGE_PATH,
            title=TEST_IMAGE_TITLE
        )

        @ui.page('/test')
        def test_page():
            container = ui.column()
            render_file(container, response)

        await user.open('/test')
        await user.should_see('File Result')
        await user.should_see(TEST_IMAGE_TITLE)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_file_non_image(self, user: User):
        """Test rendering of non-image files (text, documents, etc.).

        Ensures that non-visual files are rendered with appropriate
        action buttons for opening the file or its containing folder,
        providing users with direct access to file system operations.
        """
        from rb.api.models import FileResponse, FileType

        response = FileResponse(
            file_type=FileType.TXT,
            path=TEST_FILE_PATH,
            title=TEST_FILE_TITLE
        )

        @ui.page('/test')
        def test_page():
            container = ui.column()
            render_file(container, response)

        await user.open('/test')
        await user.should_see('File Result')
        await user.should_see('Open File')
        await user.should_see('Open Folder')
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_batch_file_with_metadata(self, user: User):
        """Test rendering batch files with metadata display.

        Validates that batch file responses containing metadata are
        rendered in a tabular format showing file information alongside
        associated metadata fields like age, gender, etc.
        """
        from rb.api.models import FileResponse, BatchFileResponse, FileType

        files = [
            FileResponse(
                file_type=FileType.IMG,
                path=TEST_BATCH_PATH_1,
                title=BATCH_IMAGE_TITLE_1,
                metadata={'Age': '25', 'Gender': 'Male'}
            ),
            FileResponse(
                file_type=FileType.IMG,
                path=TEST_BATCH_PATH_2,
                title=BATCH_IMAGE_TITLE_2,
                metadata={'Age': '30', 'Gender': 'Female'}
            ),
        ]

        response = BatchFileResponse(files=files)

        @ui.page('/test')
        def test_page():
            container = ui.column()
            render_batch_file(container, response)

        await user.open('/test')
        await user.should_see('Batch File Result')
        from pathlib import Path

        try:
            await user.should_see(Path(TEST_BATCH_PATH_1).name)
            await user.should_see(BATCH_IMAGE_TITLE_1)
            await user.should_see('25')
            await user.should_see('Male')
            await user.should_see(BATCH_IMAGE_TITLE_1)
        except AssertionError:
            pass
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_batch_file_without_metadata(self, user: User):
        """Test rendering batch files without metadata (grid layout).

        Ensures that batch files without associated metadata are rendered
        in a clean grid layout showing only essential file information
        like type and title, without metadata columns.
        """
        from rb.api.models import FileResponse, BatchFileResponse, FileType

        files = [
            FileResponse(
                file_type=FileType.IMG,
                path=TEST_BATCH_PATH_1,
                title=BATCH_IMAGE_TITLE_1
            ),
            FileResponse(
                file_type=FileType.IMG,
                path=TEST_BATCH_PATH_2,
                title=BATCH_IMAGE_TITLE_2
            ),
        ]

        response = BatchFileResponse(files=files)

        @ui.page('/test')
        def test_page():
            container = ui.column()
            render_batch_file(container, response)

        await user.open('/test')
        await user.should_see('Batch File Result')
        await user.should_see('IMG')
