from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from text_summary.summarize import extract_text, process_files


@patch(
    "text_summary.summarize.PARSERS", {".txt": MagicMock(return_value="Mocked text")}
)
def test_extract_text():
    mock_file_path = Path("mock_file.txt")
    result = extract_text(mock_file_path)
    assert result == "Mocked text"


@patch("text_summary.summarize.ensure_model_exists")
@patch("text_summary.summarize.summarize", return_value="Mocked summary")
@patch(
    "text_summary.summarize.PARSERS", {".txt": MagicMock(return_value="Mocked text")}
)
@patch("text_summary.summarize.Path.mkdir")
@patch("text_summary.summarize.Path.iterdir")
@patch("text_summary.summarize.Path.write_text")
@patch("text_summary.summarize.Path.exists", return_value=True)
@patch("text_summary.summarize.Path.is_dir", return_value=True)
def test_process_files(
    mock_is_dir,
    mock_exists,
    mock_write_text,
    mock_iterdir,
    mock_mkdir,
    mock_summarize,
    mock_ensure_model_exists,
):
    mock_input_dir = Path("input_dir")
    mock_output_dir = Path("output_dir")
    mock_model = "gemma3:1b"

    # Mock input directory contents
    mock_file = MagicMock()
    mock_file.suffix = ".txt"
    mock_file.stem = "mock_file"
    mock_file.name = "mock_file.txt"
    mock_iterdir.return_value = [mock_file]

    # Call the function
    processed_files = process_files(
        mock_model, str(mock_input_dir), str(mock_output_dir)
    )

    # Assertions
    mock_ensure_model_exists.assert_called_once_with(mock_model)
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_summarize.assert_called_once_with(mock_model, "Mocked text")
    mock_write_text.assert_called_once_with("Mocked summary", encoding="utf-8")
    assert processed_files == {str(Path(mock_output_dir) / "mock_file.txt")}


@patch("text_summary.summarize.ensure_model_exists")
@patch("text_summary.summarize.Path.exists", return_value=False)
def test_process_files_input_dir_does_not_exist(mock_exists, mock_ensure_model_exists):
    with pytest.raises(ValueError, match="Input directory 'input_dir' does not exist."):
        process_files("gemma3:1b", "input_dir", "output_dir")


@patch("text_summary.summarize.ensure_model_exists")
@patch("text_summary.summarize.Path.exists", return_value=True)
@patch("text_summary.summarize.Path.is_dir", return_value=False)
def test_process_files_input_dir_not_a_directory(
    mock_is_dir, mock_exists, mock_ensure_model_exists
):
    with pytest.raises(
        ValueError, match="Input directory 'input_dir' is not a directory."
    ):
        process_files("gemma3:1b", "input_dir", "output_dir")


@patch("text_summary.summarize.ensure_model_exists")
@patch("text_summary.summarize.PARSERS", {})
@patch(
    "text_summary.summarize.Path.iterdir", return_value=[Path("unsupported_file.xyz")]
)
@patch("text_summary.summarize.Path.mkdir")
@patch("text_summary.summarize.Path.exists", return_value=True)
@patch("text_summary.summarize.Path.is_dir", return_value=True)
def test_process_files_no_supported_files(
    mock_is_dir, mock_exists, mock_mkdir, mock_iterdir, mock_ensure_model_exists
):
    with patch("text_summary.summarize.logger.warning") as mock_warning:
        processed_files = process_files("gemma3:1b", "input_dir", "output_dir")
        assert not processed_files
        mock_warning.assert_called_once_with(
            "No files were processed. Check the input directory for supported file types."
        )
