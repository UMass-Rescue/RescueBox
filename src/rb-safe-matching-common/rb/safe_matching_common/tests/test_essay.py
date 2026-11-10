import json
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from rb.safe_matching_common.essay import (
    ESSAY_MAX_CHARS,
    ESSAY_MAX_WORDS,
    create_essay,
    create_redacted_essay,
)


def _facts(*facts: str) -> dict[str, str]:
    return {"response": json.dumps({"facts": list(facts)})}


@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_essay_requests_json_schema(generate_mock):
    generate_mock.return_value = _facts("A man stands by a car.")
    create_essay("image.jpg")
    assert generate_mock.call_args.kwargs["format"]["required"] == ["facts"]


@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_essay_packs_whole_facts_in_order(generate_mock):
    generate_mock.return_value = _facts(
        "A man in a red jacket stands by a car.",
        "word " * ESSAY_MAX_WORDS,
        "The scene is a parking lot.",
    )
    assert create_essay("image.jpg") == "A man in a red jacket stands by a car."


@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_essay_stays_within_limits(generate_mock):
    generate_mock.return_value = _facts(*["A short factual sentence here."] * 30)
    essay = create_essay("image.jpg")
    assert len(essay.split()) <= ESSAY_MAX_WORDS
    assert len(essay) <= ESSAY_MAX_CHARS
    assert essay.endswith(".")


@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_essay_rejects_invalid_json(generate_mock):
    generate_mock.return_value = {"response": "I can't help with that."}
    with pytest.raises(ValidationError):
        create_essay("image.jpg")


@patch("rb.safe_matching_common.essay.redact_text")
@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_redacted_essay_redacts_essay(generate_mock, redact_mock):
    generate_mock.return_value = _facts("A man named Bob stands by a car.")
    redact_mock.return_value = "A man named stands by a car."
    assert create_redacted_essay("image.jpg") == "A man named stands by a car."
    redact_mock.assert_called_once_with("A man named Bob stands by a car.")
