from unittest.mock import patch

from rb.safe_matching_common.essay import (
    ESSAY_MAX_CHARS,
    ESSAY_MAX_WORDS,
    create_essay,
    create_redacted_essay,
)


def _reply(text: str) -> dict[str, str]:
    return {"response": text}


@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_essay_returns_short_paragraph_unchanged(generate_mock):
    generate_mock.return_value = _reply(
        "  A man stands by a car.\nThe scene is a parking lot.  "
    )
    assert create_essay("image.jpg") == (
        "A man stands by a car. The scene is a parking lot."
    )
    assert "format" not in generate_mock.call_args.kwargs


@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_essay_keeps_whole_sentences_in_order(generate_mock):
    generate_mock.return_value = _reply(
        "A man in a red jacket stands by a car. "
        + "word " * ESSAY_MAX_WORDS
        + ". The scene is a parking lot."
    )
    assert create_essay("image.jpg") == "A man in a red jacket stands by a car."


@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_essay_stays_within_limits(generate_mock):
    generate_mock.return_value = _reply(
        " ".join(["A short factual sentence here."] * 30)
    )
    essay = create_essay("image.jpg")
    assert len(essay.split()) <= ESSAY_MAX_WORDS
    assert len(essay) <= ESSAY_MAX_CHARS
    assert essay.endswith(".")


@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_essay_cuts_oversized_first_sentence(generate_mock):
    generate_mock.return_value = _reply("longword " * 100 + ". The scene is a park.")
    essay = create_essay("image.jpg")
    assert essay
    assert len(essay.split()) <= ESSAY_MAX_WORDS
    assert len(essay) <= ESSAY_MAX_CHARS
    assert essay == essay.strip()


@patch("rb.safe_matching_common.essay.redact_text")
@patch("rb.safe_matching_common.essay.ollama.generate")
def test_create_redacted_essay_redacts_essay(generate_mock, redact_mock):
    generate_mock.return_value = _reply("A man named Bob stands by a car.")
    redact_mock.return_value = "A man named stands by a car."
    assert create_redacted_essay("image.jpg") == "A man named stands by a car."
    redact_mock.assert_called_once_with("A man named Bob stands by a car.")
