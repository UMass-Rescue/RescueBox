from unittest.mock import patch

from rb.safe_matching_common.essay import (
    ESSAY_MAX_WORDS,
    create_essay,
    create_redacted_essay,
)


@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_essay_strips_think_and_caps_words(generate_mock):
    generate_mock.return_value = {"response": "<think>plan</think> " + "word " * 80}
    essay = create_essay("image.jpg")
    assert "plan" not in essay
    assert len(essay.split()) == ESSAY_MAX_WORDS


@patch("rb.safe_matching_common.essay.redact_text")
@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_redacted_essay_redacts_essay(generate_mock, redact_mock):
    generate_mock.return_value = {"response": "A man named Bob stands by a car."}
    redact_mock.side_effect = lambda text: text.replace("Bob", "<PERSON>")
    assert create_redacted_essay("image.jpg") == "A man named <PERSON> stands by a car."
