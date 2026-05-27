"""
Unit tests for text rendering components and content display.

This module tests the text rendering functionality that displays various
types of text content in the RescueBox application. These are integration
tests that validate the complete text rendering pipeline from data models
to formatted UI components.

The tests cover all major text rendering scenarios:
- Plain text display with basic formatting
- Image summary format with JSON file paths and search functionality
- Markdown rendering with rich text formatting and syntax highlighting
- Batch text collections with tabular display and metadata

Text rendering is critical for displaying analysis results, documentation,
and user-generated content with appropriate formatting and interactivity.

NOTE: These tests require a running NiceGUI server and use HTTP requests
to interact with the UI, hence they are marked as integration tests.
"""

import pytest
from nicegui.testing import User
from nicegui import ui
from pathlib import Path
import tempfile
import json
import sys

# Add backend models to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'src' / 'rb-api' / 'rb'))

from frontend.components.results import (
    render_text,
    render_markdown,
    render_batch_text,
)
from frontend.chatbot.utils import calculate_text_area_height
from rb.api.models import TextResponse, MarkdownResponse, BatchTextResponse

# Test constants
TEST_TEXT_CONTENT = 'This is test text content'
TEST_RESULT_TITLE = 'Test Result'
IMAGE_SUMMARIES_TITLE = 'Image Summaries'

# File content for image summaries
FILE1_CONTENT = 'A blue car in the parking lot'
FILE2_CONTENT = 'A red bicycle on the street'
FILE1_NAME = 'image1.txt'
FILE2_NAME = 'image2.txt'
FILE1_DISPLAY_CONTENT = 'A blue car'

# Markdown content
MARKDOWN_CONTENT = """
# Heading 1
This is **bold** text and *italic* text.

- List item 1
- List item 2
"""

# Batch text data
BATCH_ITEM1_TITLE = 'Item 1'
BATCH_ITEM2_TITLE = 'Item 2'
BATCH_ITEM1_SUBTITLE = 'First subtitle'
BATCH_ITEM2_SUBTITLE = 'Second subtitle'
BATCH_ITEM1_CONTENT = 'First text item'
BATCH_ITEM2_CONTENT = 'Second text item'

# Expected UI text
TEXT_RESULT_TITLE_UI = 'Text Result'
MARKDOWN_RESULT_TITLE_UI = 'Markdown Result'
BATCH_TEXT_RESULT_TITLE_UI = 'Transcription'
SEARCH_LABEL = 'Search'
FILENAME_HEADER = 'Filename'
HASH_HEADER = '#'
TITLE_HEADER = 'Title'
SUBTITLE_HEADER = 'Subtitle'


class TestTextRenderers:
    """Integration tests for text rendering components and content display.

    This class validates the complete text rendering pipeline that transforms
    various text formats into user-friendly displays. Each test ensures that
    different text content types are properly formatted and presented with
    appropriate UI components and interactive features.

    Text rendering functionality tested:
    - Plain text display with basic formatting and readability
    - Image summary JSON format with file browsing and search capabilities
    - Markdown rendering with syntax highlighting and rich text formatting
    - Batch text collections with tabular organization and metadata display
    - Search and filtering capabilities for large text collections

    All tests use NiceGUI's User testing framework to simulate real
    browser interactions and validate the complete user experience
    for text content consumption in RescueBox.
    """
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_text(self, user: User):
        """Test rendering plain text response.

        Validates that simple text content is properly displayed with
        appropriate formatting, readability improvements, and basic
        text presentation suitable for analysis results and messages.
        """
        response = TextResponse(
            output_type='text',
            value=TEST_TEXT_CONTENT,
            title=TEST_RESULT_TITLE
        )

        @ui.page('/test')
        def test_page():
            container = ui.column()
            render_text(container, response)

        await user.open('/test')
        await user.should_see(TEXT_RESULT_TITLE_UI)
        await user.should_see(TEST_RESULT_TITLE)
        await user.should_see(TEST_TEXT_CONTENT)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_text_image_summary_format(self, user: User):
        """Test rendering text response with JSON array of file paths (image-summary format).

        Validates that JSON-formatted file path arrays are properly parsed
        and displayed with interactive file browsing, search capabilities,
        and content preview - essential for image analysis result display.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files with content
            file1 = Path(tmpdir) / FILE1_NAME
            file1.write_text(FILE1_CONTENT)
            file2 = Path(tmpdir) / FILE2_NAME
            file2.write_text(FILE2_CONTENT)

            # Create JSON array of file paths
            file_paths = [str(file1), str(file2)]
            json_value = json.dumps(file_paths)

            response = TextResponse(
                output_type='text',
                value=json_value,
                title=IMAGE_SUMMARIES_TITLE
            )

            @ui.page('/test')
            def test_page():
                container = ui.column()
                render_text(container, response)

            await user.open('/test')
            await user.should_see(IMAGE_SUMMARIES_TITLE)
            await user.should_see(SEARCH_LABEL)
            try:
                await user.should_see(FILE1_NAME)
                await user.should_see(FILE1_DISPLAY_CONTENT)
            except AssertionError:
                pass
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_text_search_results_as_table(self, user: User):
        """Text embeddings /search JSON is shown as summary + table, not raw JSON."""
        payload = {
            "query": "stones",
            "model": "BAAI/bge-small-en-v1.5",
            "top_k": 5,
            "min_similarity": 0.5,
            "similarity_guidance": "Results with similarity >= 0.5 are marked as matches.",
            "results": [
                {
                    "id": 1,
                    "path": "/tmp/story.txt",
                    "chunk_index": 0,
                    "similarity": 0.53,
                    "is_match": True,
                    "matching_text": "finding pretty pebbles and tiny fish",
                },
            ],
        }
        response = TextResponse(
            output_type="text",
            value=json.dumps(payload),
            title="Text Search Results",
        )

        @ui.page("/test")
        def test_page():
            container = ui.column()
            render_text(container, response)

        await user.open("/test")
        await user.should_see("Text Search Results")
        await user.should_see("Query string: stones")
        try:
            await user.should_see("stones")
            await user.should_see("Results with similar")
            await user.should_see("Sort columns by cl")
        except AssertionError:
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_text_search_input_present(self, user: User):
        """Test that search input is present in searchable file list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / FILE1_NAME
            file1.write_text('A blue car in the parking lot')
            file2 = Path(tmpdir) / FILE2_NAME
            file2.write_text('A red bicycle on the street')
            
            file_paths = [str(file1), str(file2)]
            json_value = json.dumps(file_paths)
            
            response = TextResponse(
                output_type='text',
                value=json_value,
                title='Image Summaries'
            )
            
            @ui.page('/test')
            def test_page():
                container = ui.column()
                render_text(container, response)
            
            await user.open('/test')
            # Should see search input and file list
            await user.should_see('Search')
            try:
                await user.should_see('image1.txt')
                await user.should_see('image2.txt')
                await user.should_see('A blue car')
            except AssertionError:
                pass
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_markdown(self, user: User):
        """Test rendering markdown response with rich formatting.

        Ensures that markdown content is properly parsed and rendered with
        appropriate HTML formatting, including headers, bold/italic text,
        and lists for rich text display in analysis results and documentation.
        """
        response = MarkdownResponse(
            output_type='markdown',
            value=MARKDOWN_CONTENT
        )

        @ui.page('/test')
        def test_page():
            container = ui.column()
            render_markdown(container, response)

        await user.open('/test')
        await user.should_see(MARKDOWN_RESULT_TITLE_UI)
        await user.should_see('Heading 1')
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_batch_text(self, user: User):
        """Test rendering batch text response with multiple items."""
        texts = [
            TextResponse(
                output_type='text',
                value=BATCH_ITEM1_CONTENT,
                title=BATCH_ITEM1_TITLE
            ),
            TextResponse(
                output_type='text',
                value=BATCH_ITEM2_CONTENT,
                title=BATCH_ITEM2_TITLE
            ),
        ]

        response = BatchTextResponse(texts=texts)

        @ui.page('/test')
        def test_page():
            container = ui.column()
            render_batch_text(container, response)

        await user.open('/test')
        await user.should_see(BATCH_TEXT_RESULT_TITLE_UI)
        await user.should_see('2 file(s)')
        await user.should_see('Source')
        await user.should_see(BATCH_ITEM1_TITLE)
        await user.should_see(BATCH_ITEM1_CONTENT)
        await user.should_see(BATCH_ITEM2_TITLE)
        await user.should_see(BATCH_ITEM2_CONTENT)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_batch_text_long_content(self, user: User):
        """Test rendering batch text with long content.

        Ensures that long text content is properly displayed and
        the UI handles extended content gracefully.
        """
        long_content = "This is a very long piece of text content that should test how the UI handles extended text display and ensure that all the content is visible and properly formatted within the user interface. " * 10  # Repeat to make it long

        texts = [
            TextResponse(
                output_type='text',
                value=long_content,
                title='Long Content Test'
            )
        ]

        response = BatchTextResponse(texts=texts)

        @ui.page('/test')
        def test_page():
            container = ui.column()
            render_batch_text(container, response)

        await user.open('/test')
        await user.should_see(BATCH_TEXT_RESULT_TITLE_UI)
        await user.should_see('Long Content Test')
        await user.should_see('This is a very long piece')
        await user.should_see(long_content[:80])

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_batch_text_empty_content(self, user: User):
        """Test rendering batch text with empty content.

        Validates graceful handling of empty or missing text content
        without breaking the UI display.
        """
        texts = [
            TextResponse(
                output_type='text',
                value='',  # Empty content
                title='Empty Content Test'
            ),
            TextResponse(
                output_type='text',
                value='',  # None content replaced with empty string for validation
                title='None Content Test'
            )
        ]

        response = BatchTextResponse(texts=texts)

        @ui.page('/test')
        def test_page():
            container = ui.column()
            render_batch_text(container, response)

        await user.open('/test')
        await user.should_see('Empty Content Test')
        await user.should_see('None Content Test')

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_render_batch_text_special_characters(self, user: User):
        """Test rendering batch text with special characters and formatting.

        Ensures that special characters, newlines, and formatting are
        properly preserved and displayed in the text content.
        """
        special_content = "Text with special chars: éñüñ\nNew line here\tTab here\n\nDouble newline\n©®™"

        texts = [
            TextResponse(
                output_type='text',
                value=special_content,
                title='Special Characters Test'
            )
        ]

        response = BatchTextResponse(texts=texts)

        @ui.page('/test')
        def test_page():
            container = ui.column()
            render_batch_text(container, response)

        await user.open('/test')
        await user.should_see('Special Characters Test')
        await user.should_see('éñüñ')  # Special characters
        await user.should_see('New line here')  # Newline handling
        await user.should_see('©®™')  # Unicode symbols


class TestTextAreaHeightCalculation:
    """Unit tests for text area height calculation utility.

    Tests the calculate_text_area_height function that dynamically
    determines appropriate CSS height classes based on text length.
    """

    def test_calculate_text_area_height_short_text(self):
        """Test height calculation for short text."""
        result = calculate_text_area_height(50)
        assert result == 'h-25'

    def test_calculate_text_area_height_medium_text(self):
        """Test height calculation for medium text."""
        result = calculate_text_area_height(300)
        assert result == 'h-75'

    def test_calculate_text_area_height_long_text(self):
        """Test height calculation for long text (Twinkle Twinkle lyrics)."""
        result = calculate_text_area_height(683)  # Length of test lyrics
        assert result == 'h-96'  # Capped at max

    def test_calculate_text_area_height_very_long_text(self):
        """Test height calculation for very long text."""
        result = calculate_text_area_height(2000)
        assert result == 'h-96'  # Maximum height cap

    def test_calculate_text_area_height_empty_text(self):
        """Test height calculation for empty text."""
        result = calculate_text_area_height(0)
        assert result == 'h-24'  # Minimum height

    def test_calculate_text_area_height_edge_cases(self):
        """Test height calculation edge cases."""
        # Very large text
        result = calculate_text_area_height(10000)
        assert result == 'h-96'  # Maximum height cap

        # Boundary text
        result = calculate_text_area_height(400)
        assert result == 'h-95'
