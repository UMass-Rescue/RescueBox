"""
Unit tests for table helper utilities
"""

import pytest
from nicegui import ui
from nicegui.testing import User

from frontend.components.results import (
    create_directory_row_click_handler,
    create_file_row_click_handler,
    create_metadata_table_columns,
    create_sortable_table,
)
from frontend.components.results.table_helpers import (
    PREVIEW_UNAVAILABLE_LABEL,
    display_filename,
    enrich_row_with_thumbnail,
    is_image_result_row,
    is_previewable_image,
    json_storage_key,
    looks_like_json_object,
    metadata_field_key,
)


class TestTableHelpers:
    """Tests for table helper utilities"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_sortable_table(self, user: User):
        """Test creating a sortable table"""
        columns = [
            {
                "name": "col1",
                "label": "Column 1",
                "field": "col1",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "col2",
                "label": "Column 2",
                "field": "col2",
                "align": "left",
                "sortable": True,
            },
        ]
        rows = [
            {"col1": "value1", "col2": "value2"},
            {"col1": "value3", "col2": "value4"},
        ]

        @ui.page("/test")
        def test_page():
            container = ui.column()
            create_sortable_table(
                container,
                columns,
                rows,
                row_key="col1",
                show_row_labels=True,
            )

        await user.open("/test")
        # Column header labels are not duplicated as visible text; row labels are.
        await user.should_see("value1")
        await user.should_see("value2")
        await user.should_see("value3")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_sortable_table_with_tip(self, user: User):
        """Test creating a sortable table with tip message"""
        columns = [
            {
                "name": "col1",
                "label": "Column 1",
                "field": "col1",
                "align": "left",
                "sortable": True,
            }
        ]
        rows = [{"col1": "value1"}]

        @ui.page("/test")
        def test_page():
            container = ui.column()
            create_sortable_table(
                container, columns, rows, row_key="col1", tip_message="Test tip message"
            )

        await user.open("/test")
        await user.should_see("Test tip message")

    def test_metadata_field_key(self):
        assert metadata_field_key("Imported") == "imported"
        assert json_storage_key("imported") == "_json_imported"

    def test_looks_like_json_object(self):
        assert looks_like_json_object('{"content_sha256": "abc"}') is True
        assert looks_like_json_object("not json") is False
        assert looks_like_json_object("[1, 2]") is False

    def test_is_previewable_image(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"x")
        assert is_previewable_image(str(img)) is True
        assert is_previewable_image(str(tmp_path / "missing.jpg")) is False
        assert is_previewable_image("photo.jpg") is False

    def test_display_filename(self):
        assert display_filename("/tmp/photo.jpg") == "photo.jpg"
        assert display_filename("No filepath provided") == PREVIEW_UNAVAILABLE_LABEL
        assert display_filename("") == PREVIEW_UNAVAILABLE_LABEL

    def test_is_image_result_row_imported_metadata(self):
        assert is_image_result_row(
            "vacation.jpg",
            metadata={"Source": '{"content_sha256": "abc"}'},
        )
        assert is_image_result_row(
            "photo.jpg",
            metadata={"Source": "Local", "Embedding type": "Plain (original image)"},
        )
        assert not is_image_result_row("report.txt", metadata={"Source": "Local"})

    def test_enrich_row_with_thumbnail(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"x")
        row = enrich_row_with_thumbnail({"path_full": str(img), "path": img.name})
        assert row["thumbnail_url"].startswith("/_serve/")
        imported = enrich_row_with_thumbnail(
            {"path_full": "vacation.jpg", "path": "vacation.jpg"},
            metadata={"Source": "Local"},
        )
        assert imported["preview_unavailable"] is True
        plain = enrich_row_with_thumbnail(
            {"path_full": "notes.txt", "path": "notes.txt"},
        )
        assert "thumbnail_url" not in plain
        assert "preview_unavailable" not in plain

    def test_create_metadata_table_columns(self):
        """Test creating columns with metadata keys"""
        base_columns = [
            {
                "name": "path",
                "label": "Path",
                "field": "path",
                "align": "left",
                "sortable": True,
            },
            {
                "name": "title",
                "label": "Title",
                "field": "title",
                "align": "left",
                "sortable": True,
            },
        ]
        metadata_keys = ["Age", "Gender", "Bounding Box"]

        columns = create_metadata_table_columns(base_columns, metadata_keys)

        assert len(columns) == 5  # 2 base + 3 metadata
        assert columns[0]["name"] == "path"
        assert columns[2]["name"] == "age"
        assert columns[2]["label"] == "Age"
        assert columns[3]["label"] == "Gender"
        assert all(col["sortable"] for col in columns)

    def test_create_file_row_click_handler(self):
        """Test creating file row click handler"""
        rows = [
            {"path_full": "/path/to/file1.txt", "filename": "file1.txt"},
            {"path_full": "/path/to/file2.txt", "filename": "file2.txt"},
        ]

        clicked_paths = []

        def mock_open_file(path):
            clicked_paths.append(path)

        handler = create_file_row_click_handler(rows, mock_open_file)

        # Simulate click on first row (index 0)
        class MockEvent:
            def __init__(self):
                self.args = [None, 0]  # row index is second arg

        handler(MockEvent())
        assert clicked_paths == ["/path/to/file1.txt"]

    def test_create_directory_row_click_handler(self):
        """Test creating directory row click handler"""
        rows = [
            {"path_full": "/path/to/dir1", "path": "dir1"},
            {"path_full": "/path/to/dir2", "path": "dir2"},
        ]

        clicked_paths = []

        def mock_open_folder(path):
            clicked_paths.append(path)

        handler = create_directory_row_click_handler(rows, mock_open_folder)

        # Simulate click on second row (index 1)
        class MockEvent:
            def __init__(self):
                self.args = [None, 1]  # row index is second arg

        handler(MockEvent())
        assert len(clicked_paths) == 1
        assert clicked_paths[0] == "/path/to/dir2"

    def test_create_file_row_click_handler_fallback_to_path(self):
        """Test file row click handler falls back to 'path' if 'path_full' not present"""
        rows = [
            {"path": "/path/to/file1.txt", "filename": "file1.txt"},  # No path_full
        ]

        clicked_paths = []

        def mock_open_file(path):
            clicked_paths.append(path)

        handler = create_file_row_click_handler(rows, mock_open_file)

        class MockEvent:
            def __init__(self):
                self.args = [None, 0]

        handler(MockEvent())
        assert clicked_paths == ["/path/to/file1.txt"]
