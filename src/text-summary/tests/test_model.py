import pytest
from unittest.mock import patch, MagicMock
from text_summary.model import (
    extract_response_after_think,
    ensure_model_exists,
    summarize,
)
from text_summary.summary_prompt import PROMPT
from ollama._types import ListResponse


def test_extract_response_after_think():
    # Test case where </think> tag is present
    text_with_tag = "Some text</think>Extracted text"
    assert extract_response_after_think(text_with_tag) == "Extracted text"

    # Test case where </think> tag is not present
    text_without_tag = "Some text without tag"
    assert extract_response_after_think(text_without_tag) == text_without_tag.strip()


@patch("ollama.list")
@patch("ollama.pull")
# @patch.object(ollama.Client, '__init__', return_value=None)
def test_ensure_model_exists(mock_pull, mock_list):
    # Test case where model is supported and pull is successful

    mock_pull.return_value = MagicMock(status="success")

    mock_list.return_value = {"models": [ListResponse.Model(model="gemma3:1b")]}
    ensure_model_exists("gemma3:1b")  # Should not raise any exception

    # Test case where model is not supported
    with pytest.raises(ValueError, match="Model 'unsupported_model' is not supported."):
        ensure_model_exists("unsupported_model")

    # Test case where pull fails
    mock_pull.return_value = MagicMock(status="failure")
    with pytest.raises(ValueError, match="Failed to pull model 'llama3.2:3b'"):
        ensure_model_exists("llama3.2:3b")


@patch("text_summary.model.ollama.generate")
def test_summarize(mock_generate):
    # Test case where response is successful
    mock_generate.return_value = {
        "done": True,
        "response": "Some response</think>Summary",
    }
    result = summarize("gemma3:1b", "Some text")
    assert result == "Summary"
    mock_generate.assert_called_once_with("gemma3:1b", PROMPT.format(text="Some text"))

    # Test case where response is not done
    mock_generate.return_value = {"done": False}
    result = summarize("gemma3:1b", text="Some text")
    assert result == {"done": False}
