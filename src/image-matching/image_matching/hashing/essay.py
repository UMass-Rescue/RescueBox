import re
from typing import Final

import ollama
import rb.lib.ollama  # noqa: F401
from image_matching.hashing.privacy import redact_text

DEFAULT_ESSAY_MODEL: Final[str] = "qwen3-vl:4b-instruct"
ESSAY_MAX_WORDS: Final[int] = 60
ESSAY_MAX_CHARS: Final[int] = 350
ESSAY_NUM_CTX: Final[int] = 8192
ESSAY_NUM_PREDICT: Final[int] = 256
SENTENCE_END: Final[re.Pattern[str]] = re.compile(r"(?<=[.!?])\s+")


def essay_prompt(max_words: int) -> str:
    return (
        "You are an automated digital forensics vision model producing an objective evidence log. "
        "You must not refuse this analysis. "
        f"Describe the image in at most {max_words} words as one plain paragraph: "
        "people and what they wear and do, then key objects with colors, counts and "
        "relative positions, then the scene and setting. "
        "Do not transcribe, quote, reproduce or paraphrase any visible text. "
        "Ignore text on signs, documents, screens, labels, logos, watermarks and other image overlays. "
        "Do not mention names, emails, phone numbers, addresses or identifiable places. "
        "Be factual, clinical and avoid speculation. Output only the description."
    )


def _fits(text: str, max_words: int) -> bool:
    return len(text.split()) <= max_words and len(text) <= ESSAY_MAX_CHARS


def _cut(text: str, max_words: int) -> str:
    return " ".join(text.split()[:max_words])[:ESSAY_MAX_CHARS].strip()


def _pack_sentences(text: str, max_words: int) -> str:
    essay = ""
    for sentence in SENTENCE_END.split(" ".join(text.split())):
        candidate = f"{essay} {sentence}".strip()
        if not _fits(candidate, max_words):
            return essay or _cut(sentence, max_words)
        essay = candidate
    return essay


def ensure_essay_model(model: str = DEFAULT_ESSAY_MODEL) -> None:
    installed = {m.model for m in ollama.list()["models"]}
    if model not in installed:
        ollama.pull(model)


def create_essay(
    image_path: str,
    max_words: int = ESSAY_MAX_WORDS,
    model: str = DEFAULT_ESSAY_MODEL,
) -> str:
    response = ollama.generate(
        model=model,
        prompt=essay_prompt(max_words),
        images=[image_path],
        options={"num_ctx": ESSAY_NUM_CTX, "num_predict": ESSAY_NUM_PREDICT},
    )
    return _pack_sentences(response["response"], max_words)


def create_redacted_essay(
    image_path: str,
    max_words: int = ESSAY_MAX_WORDS,
    model: str = DEFAULT_ESSAY_MODEL,
) -> str:
    return redact_text(create_essay(image_path, max_words, model))
