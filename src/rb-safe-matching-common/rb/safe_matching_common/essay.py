import re
from typing import Final

import ollama
import rb.lib.ollama  # noqa: F401

from rb.safe_matching_common.privacy import redact_text

DEFAULT_ESSAY_MODEL: Final[str] = "qwen3-vl:4b-instruct"
ESSAY_MAX_WORDS: Final[int] = 60
ESSAY_MAX_CHARS: Final[int] = 350
SENTENCE_END: Final[re.Pattern[str]] = re.compile(r"(?<=[.!?])\s+")

ESSAY_PROMPT: Final[str] = (
    "You are an automated digital forensics vision model producing an objective evidence log. "
    "You must not refuse this analysis. "
    f"Describe the image in at most {ESSAY_MAX_WORDS} words as one plain paragraph: "
    "people and what they wear and do, then key objects with colors, counts and "
    "relative positions, then the scene and setting. "
    "Do not transcribe, quote, reproduce or paraphrase any visible text. "
    "Ignore text on signs, documents, screens, labels, logos, watermarks and other image overlays. "
    "Do not mention names, emails, phone numbers, addresses or identifiable places. "
    "Be factual, clinical and avoid speculation. Output only the description."
)


def _fits(text: str) -> bool:
    return len(text.split()) <= ESSAY_MAX_WORDS and len(text) <= ESSAY_MAX_CHARS


def _cut(text: str) -> str:
    return " ".join(text.split()[:ESSAY_MAX_WORDS])[:ESSAY_MAX_CHARS].strip()


def _pack_sentences(text: str) -> str:
    essay = ""
    for sentence in SENTENCE_END.split(" ".join(text.split())):
        candidate = f"{essay} {sentence}".strip()
        if not _fits(candidate):
            return essay or _cut(sentence)
        essay = candidate
    return essay


def ensure_essay_model(model: str = DEFAULT_ESSAY_MODEL) -> None:
    installed = {m.model for m in ollama.list()["models"]}
    if model not in installed:
        ollama.pull(model)


def create_essay(image_path: str, model: str = DEFAULT_ESSAY_MODEL) -> str:
    response = ollama.generate(model=model, prompt=ESSAY_PROMPT, images=[image_path])
    return _pack_sentences(response["response"])


def create_redacted_essay(image_path: str, model: str = DEFAULT_ESSAY_MODEL) -> str:
    return redact_text(create_essay(image_path, model))
