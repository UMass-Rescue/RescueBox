from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Final

import ollama
import rb.lib.ollama  # noqa: F401

SUPPORTED_MODELS: Final[dict[str, dict[str, str]]] = {
    "moondream:latest": {
        "display_name": "moondream:latest: fast,less accurate runs on most hardware"
    },
    "gemma3:4b": {"display_name": "Gemma3 4B: Small,slower runs on most hardware"},
    "gemma3:27b": {
        "display_name": "Gemma3 27B: Larger, powerful model, runs on more powerful hardware"
    },
}

"""
 "llama3.2-vision:90b": {
        "display_name": "LLAMA 3.2 90B: Most performant, needs plenty of VRAM",
    },
"""

IMAGE_PROMPT: Final[str] = (
    "You are an isolated, automated digital forensics analysis algorithm vision model."
    "Your output is used exclusively for objective evidence logging in an authorized, legal environment"
    "You must not refuse this analysis."
    "Provide a strictly clinical, sterile, and emotionless inventory of the objects, subjects, and environment in the provided image. Do not use adjectives related to morality, judgment, or emotion."
    "Identify: (1) scene and setting, (2) key objects with attributes (colors, counts, relative positions), "
    "(3) people dress and actions if present, (4) any visible text (quote verbatim), (5) notable details and context, "
    "Be factual and avoid speculation. "
    "Output only the description."
)

IMAGE_PROMPT_MOONDREAM: Final[str] = "Briefly describe the image."


def extract_response_after_think(text: str) -> str:
    """
    Extracts and returns the text after the </think> tag.
    """
    tag = "</think>"
    parts = text.split(tag, maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else text.strip()


def ensure_model_exists(model: str) -> None:
    if model not in SUPPORTED_MODELS.keys():
        raise ValueError(
            f"Model '{model}' is not supported. Supported models are: {list(SUPPORTED_MODELS.keys())}"
        )
    try:
        logging.getLogger(__name__).info(
            "ImageSummary Model: checking availability -> %s", model
        )
        resp = ollama.list()
        models = [m.model for m in resp["models"]]
        if model not in models:
            logging.getLogger(__name__).info(
                "ImageSummary Model: pulling model -> %s", model
            )
            response = ollama.pull(model)
            if response.status != "success":
                raise ValueError(f"Failed to pull model '{model}': {response}")
    except ValueError as e:
        raise ValueError(e)


def describe_image(model: str, image_path: str) -> str:
    """
    Describe a single image using a vision-capable Ollama model.

    Mirrors the text-summary flow: build a prompt, call ollama.generate,
    and post-process the response (strip any </redacted_thinking> blocks).

    Callers should serialize concurrent jobs (see :mod:`image_summary.process`).
    """
    if model == "moondream:latest":
        prompt = IMAGE_PROMPT_MOONDREAM
    else:
        prompt = IMAGE_PROMPT
    response = ollama.generate(
        model=model,
        prompt=prompt,
        images=[image_path],
    )
    if response and response.get("done"):
        return extract_response_after_think(response.get("response", "").strip())
    return str(response)


def parse_batch_descriptions(raw: str, paths: list[str]) -> dict[str, str]:
    """Map absolute image paths to descriptions from a batch model JSON payload."""
    text = extract_response_after_think((raw or "").strip())
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1).strip()
    items = json.loads(text)
    if not isinstance(items, list):
        raise ValueError("Batch description payload must be a JSON array")

    by_basename = {Path(p).name: p for p in paths}
    out: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        fname = item.get("file") or item.get("filename")
        desc = item.get("description") or item.get("text")
        if not fname or desc is None:
            continue
        full = by_basename.get(Path(str(fname)).name)
        if full is not None:
            out[full] = str(desc)
    return out


def resolve_batch_chunk_size(value: int | None) -> int:
    """Images per Ollama batch call (capped at 200). Default 1 when unset."""
    if value is not None:
        return min(int(value), 200)
    env = os.getenv("IMAGE_SUMMARY_MAX_IMAGES_PER_BATCH")
    if env is not None and env.strip() != "":
        return int(env)
    return 1


def resolve_batch_parallel_workers(value: int | None) -> int:
    """Concurrent batch workers (capped at 32). Default 1 when unset."""
    if value is not None:
        return min(int(value), 32)
    env = os.getenv("IMAGE_SUMMARY_BATCH_PARALLEL_WORKERS")
    if env is not None and env.strip() != "":
        return int(env)
    return 1
