"""Unit tests for frontend.chatbot.granite.parse_fine_tune_tool_response."""

import json

from frontend.chatbot.granite import parse_fine_tune_tool_response


def test_three_separate_tool_code_tags():
    calls = [
        {"name": "age-gender/predict", "arguments": {"image_directory": "/evidence/batch2"}},
        {
            "name": "image_summary/summarize-images",
            "arguments": {
                "input_dir": "/evidence/batch2",
                "output_dir": "/evidence/batch2/summary",
                "model": "gemma3:4b",
            },
        },
        {"name": "text_embeddings/search", "arguments": {"input_dir": "/evidence/batch2/summary", "query": "boy"}},
    ]
    text = "".join(f"<tool_code>{json.dumps(c)}</tool_code>\n" for c in calls)
    out = parse_fine_tune_tool_response(text)
    assert out is not None
    assert len(out) == 3
    assert out[2]["name"] == "text_embeddings/search"


def test_single_tool_code_with_calls_array():
    payload = {"calls": [{"name": "a", "arguments": {"x": 1}}, {"name": "b", "arguments": {"y": 2}}]}
    text = f"<tool_code>{json.dumps(payload)}</tool_code>"
    out = parse_fine_tune_tool_response(text)
    assert out is not None
    assert len(out) == 2


def test_single_tool_code_with_top_level_array():
    payload = [
        {"name": "age-gender/predict", "arguments": {"image_directory": "/tmp"}},
        {"name": "text_embeddings/search", "arguments": {"input_dir": "/tmp/s", "query": "q"}},
    ]
    text = f"<tool_code>{json.dumps(payload)}</tool_code>"
    out = parse_fine_tune_tool_response(text)
    assert out is not None
    assert len(out) == 2


def test_raw_json_calls_no_tags():
    payload = {
        "calls": [
            {"name": "image_summary/summarize-images", "arguments": {"input_dir": "/a", "output_dir": "/a/o", "model": "gemma3:4b"}}
        ]
    }
    out = parse_fine_tune_tool_response(json.dumps(payload))
    assert out is not None
    assert len(out) == 1


def test_empty_whitespace():
    assert parse_fine_tune_tool_response("") is None
    assert parse_fine_tune_tool_response("   ") is None
