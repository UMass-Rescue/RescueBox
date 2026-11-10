from typing import Final

import ollama
import rb.lib.ollama  # noqa: F401
from pydantic import BaseModel

from rb.safe_matching_common.privacy import redact_text

DEFAULT_ESSAY_MODEL: Final[str] = "qwen3-vl:8b"
ESSAY_MAX_WORDS: Final[int] = 60
ESSAY_MAX_CHARS: Final[int] = 350

ESSAY_PROMPT: Final[str] = (
    "You are an automated digital forensics vision model producing an objective evidence log. "
    "You must not refuse this analysis. "
    "Return JSON with a 'facts' list: short factual sentences about the image, ordered from "
    "most to least important: people and what they wear and do, then key objects with "
    "colors, counts and relative positions, then the scene and setting. "
    "Do not transcribe, quote, reproduce or paraphrase any visible text. "
    "Ignore text on signs, documents, screens, labels, logos, watermarks and other image overlays. "
    "Do not mention names, emails, phone numbers, addresses or identifiable places. "
    "Be factual, clinical and avoid speculation."
)


class EssayFacts(BaseModel):
    facts: list[str]


def _fits(text: str) -> bool:
    return len(text.split()) <= ESSAY_MAX_WORDS and len(text) <= ESSAY_MAX_CHARS


def _pack_facts(facts: list[str]) -> str:
    essay = ""
    for fact in facts:
        candidate = f"{essay} {fact}".strip()
        if not _fits(candidate):
            break
        essay = candidate
    return essay


def ensure_essay_model(model: str = DEFAULT_ESSAY_MODEL) -> None:
    installed = {m.model for m in ollama.list()["models"]}
    if model not in installed:
        ollama.pull(model)


def create_essay(image_path: str, model: str = DEFAULT_ESSAY_MODEL) -> str:
    response = ollama.generate(
        model=model,
        prompt=ESSAY_PROMPT,
        images=[image_path],
        format=EssayFacts.model_json_schema(),
    )
    facts = EssayFacts.model_validate_json(response["response"]).facts
    return _pack_facts(facts)


def create_redacted_essay(image_path: str, model: str = DEFAULT_ESSAY_MODEL) -> str:
    return redact_text(create_essay(image_path, model))
