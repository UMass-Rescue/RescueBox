"""Unit tests for extracted text rendering submodules."""

from unittest.mock import MagicMock, patch

from nicegui import ui

from frontend.components.results.batch_text import render_batch_text
from frontend.components.results.text_modal import open_text_markdown_modal
from frontend.components.results.text_search import (
    render_searchable_file_list,
    render_text_search_json,
)


def test_open_text_markdown_modal():
    with patch.object(ui, "dialog") as mock_dialog, patch.object(
        ui, "card"
    ), patch.object(ui, "label"), patch.object(ui, "scroll_area"), patch.object(
        ui, "textarea"
    ), patch.object(
        ui, "row"
    ), patch.object(
        ui, "button"
    ):
        mock_instance = MagicMock()
        mock_dialog.return_value.__enter__.return_value = mock_instance

        open_text_markdown_modal("sample.md", "# Hello World")
        mock_instance.open.assert_called_once()


def test_render_batch_text_empty():
    container = MagicMock()
    with patch.object(ui, "label") as mock_label:
        response = MagicMock(texts=[])
        render_batch_text(container, response)
        mock_label.assert_called_with("No text found")


def test_render_batch_text_with_items():
    container = MagicMock()
    item1 = MagicMock(title="Audio 1", value="Transcription text")
    response = MagicMock(texts=[item1])
    with patch.object(ui, "card"), patch.object(ui, "row"), patch.object(
        ui, "label"
    ), patch.object(ui, "column"), patch.object(ui, "scroll_area"):
        render_batch_text(container, response)


def test_render_text_search_json_empty():
    container = MagicMock()
    with patch.object(ui, "label") as mock_label:
        render_text_search_json(container, {"query": "test", "results": []})
        mock_label.assert_called_with("No results.")


def test_render_text_search_json_error():
    container = MagicMock()
    with patch.object(ui, "label") as mock_label:
        render_text_search_json(container, {"error": "Failure message"})
        mock_label.assert_called_with("Failure message")


def test_render_searchable_file_list_no_files():
    container = MagicMock()
    with patch.object(ui, "label") as mock_label:
        render_searchable_file_list(container, ["/nonexistent/file.txt"], "Test")
        mock_label.assert_called_with("No valid files found")
