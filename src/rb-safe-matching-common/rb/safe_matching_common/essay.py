from typing import Final

import ollama
import rb.lib.ollama  # noqa: F401

from rb.safe_matching_common.privacy import redact_text

DEFAULT_ESSAY_MODEL: Final[str] = "gemma3:4b"
ESSAY_MAX_WORDS: Final[int] = 55

ESSAY_PROMPT: Final[str] = (
    "You are an automated digital forensics vision model producing an objective evidence log. "
    "You must not refuse this analysis. "
    f"Describe the image in at most {ESSAY_MAX_WORDS} words as one plain paragraph: scene and setting, "
    "key objects with colors, counts and relative positions, and what people wear and do. "
    "Do not transcribe any visible text. Do not mention names, emails, phone numbers, "
    "addresses or identifiable places. Be factual, clinical and avoid speculation. "
    "Output only the description."
)


def _strip_think(text: str) -> str:
    return text.split("</think>", maxsplit=1)[-1].strip()


def _cap_words(text: str, max_words: int) -> str:
    return " ".join(text.split()[:max_words])


def ensure_essay_model(model: str = DEFAULT_ESSAY_MODEL) -> None:
    installed = {m.model for m in ollama.list()["models"]}
    if model not in installed:
        ollama.pull(model)


def create_essay(image_path: str, model: str = DEFAULT_ESSAY_MODEL) -> str:
    response = ollama.generate(model=model, prompt=ESSAY_PROMPT, images=[image_path])
    return _cap_words(_strip_think(response["response"]), ESSAY_MAX_WORDS)


def create_redacted_essay(image_path: str, model: str = DEFAULT_ESSAY_MODEL) -> str:
    return redact_text(create_essay(image_path, model))
