from __future__ import annotations

import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Final

import ollama

# Max images per single Ollama generate() call (JSON + context limits; large batches drop entries).
DEFAULT_MAX_IMAGES_PER_BATCH: Final[int] = 16
_ENV_CHUNK_KEY: Final[str] = "IMAGE_SUMMARY_MAX_IMAGES_PER_BATCH"
_MAX_CHUNK_CAP: Final[int] = 200
_ENV_PARALLEL_KEY: Final[str] = "IMAGE_SUMMARY_BATCH_PARALLEL_WORKERS"
_DEFAULT_PARALLEL_WORKERS: Final[int] = 5

SUPPORTED_MODELS: Final[dict[str, dict[str, str]]] = {
    "gemma3:4b": {"display_name": "Gemma3 4B: Small, runs on more hardware"},
    "llama3.2-vision:11b": {
        "display_name": "Llama 3.2 11B: More performant, still fits into consumer GPUs",
    },
    "gemma3:27b": {"display_name": "Gemma3 27B: Larger, powerful model"},
    "llama3.2-vision:90b": {
        "display_name": "LLAMA 3.2 90B: Most performant, needs plenty of VRAM",
    },
}

IMAGE_PROMPT: Final[str] = (
    "You are a vision model. Provide a detailed description of the image. "
    "Identify: (1) scene and setting, (2) key objects with attributes (colors, counts, relative positions), "
    "(3) people dress and actions if present, (4) any visible text (quote verbatim), (5) notable details and context, "
    "(6) lighting, camera angle, and composition if apparent. Be factual and avoid speculation. "
    "Output only the description."
)

IMAGE_BATCH_PROMPT: Final[str] = (
    "You are a vision model. "
    "You will receive multiple images in the same order as listed below.\n"
    "For EACH image, write a detailed description covering: (1) scene and setting, "
    "(2) key objects with attributes (colors, counts, relative positions), "
    "(3) people dress and actions if present, (4) any visible text (quote verbatim), "
    "(5) notable details and context, (6) lighting, camera angle, and composition if apparent. "
    "Be factual and avoid speculation.\n\n"
    "Image order (first image = item 1, etc.):\n{file_list}\n\n"
    'Respond with ONLY valid JSON: a JSON array of objects. Each object must have exactly two string keys: '
    '"file" (the exact filename from the list above, including extension) and '
    '"description" (the description for that image only). '
    "Include exactly one object per image, in the same order as the list. "
    "Do not wrap the JSON in markdown code fences or add any text before or after the array."
)


def extract_response_after_think(text: str) -> str:
    """
    Extracts and returns the text after the </think> tag.
    """
    tag = "</think>"
    parts = text.split(tag, maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else text.strip()


def _strip_json_code_fence(text: str) -> str:
    s = text.strip()
    if not s.startswith("```"):
        return s
    lines = s.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_batch_descriptions(raw: str, ordered_paths: list[str]) -> dict[str, str]:
    """
    Parse model output into one description per input path.

    Expects a JSON array of {"file": "<basename>", "description": "..."}.
    Keys in the returned dict match the strings in ``ordered_paths`` exactly.
    """
    text = extract_response_after_think(raw.strip())
    text = _strip_json_code_fence(text)

    data: object | None = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\[[\s\S]*\]", text)
        if m:
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                data = None

    if not isinstance(data, list):
        raise ValueError("Batch response was not a JSON array")

    by_basename: dict[str, str] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        fn = item.get("file") or item.get("filename")
        desc = item.get("description") or item.get("text")
        if isinstance(fn, str) and isinstance(desc, str):
            by_basename[Path(fn).name] = desc.strip()

    result: dict[str, str] = {}
    for p in ordered_paths:
        name = Path(p).name
        desc = by_basename.get(name)
        if desc is None:
            for k, v in by_basename.items():
                if k.lower() == name.lower():
                    desc = v
                    break
        result[p] = desc if desc is not None else ""

    missing = [Path(p).name for p, d in result.items() if not d.strip()]
    if missing:
        logging.getLogger(__name__).warning(
            "Batch parse: missing or empty descriptions for: %s", missing
        )

    return result


def resolve_batch_chunk_size(explicit: int | None = None) -> int:
    """
    Images per Ollama batch request.

    ``explicit`` wins when set and positive (capped). Otherwise uses env
    ``IMAGE_SUMMARY_MAX_IMAGES_PER_BATCH`` (default 50), clamped to ``[1, _MAX_CHUNK_CAP]``.
    """
    if explicit is not None:
        try:
            n = int(explicit)
            if n > 0:
                return min(n, _MAX_CHUNK_CAP)
        except (TypeError, ValueError):
            pass
    raw = os.environ.get(_ENV_CHUNK_KEY, str(DEFAULT_MAX_IMAGES_PER_BATCH))
    try:
        n = int(raw.strip())
    except ValueError:
        n = DEFAULT_MAX_IMAGES_PER_BATCH
    return max(1, min(n, _MAX_CHUNK_CAP))


def resolve_batch_parallel_workers(explicit: int | None = None) -> int:
    """
    Max concurrent Ollama batch chunk requests (thread pool size).

    Capped at chunk count at call site. Env ``IMAGE_SUMMARY_BATCH_PARALLEL_WORKERS``
    overrides default ``_DEFAULT_PARALLEL_WORKERS`` (5) when unset.
    """
    if explicit is not None:
        try:
            w = int(explicit)
            if w > 0:
                return min(w, 32)
        except (TypeError, ValueError):
            pass
    raw = os.environ.get(_ENV_PARALLEL_KEY, str(_DEFAULT_PARALLEL_WORKERS))
    try:
        w = int(raw.strip())
    except ValueError:
        w = _DEFAULT_PARALLEL_WORKERS
    return max(1, min(w, 32))


def _describe_chunk_worker(model: str, chunk: list[str]) -> dict[str, str]:
    """Run in a thread: one single-image describe or one multi-image Ollama batch."""
    if len(chunk) == 1:
        p = chunk[0]
        return {p: describe_image(model, p)}
    return _describe_images_one_ollama_batch(model, chunk)


def _describe_images_one_ollama_batch(model: str, image_paths: list[str]) -> dict[str, str]:
    """Single multi-image Ollama call (``len(image_paths) >= 2``)."""
    file_list = "\n".join(f"{i + 1}. {Path(p).name}" for i, p in enumerate(image_paths))
    prompt = IMAGE_BATCH_PROMPT.format(file_list=file_list)
    response = ollama.generate(
        model=model,
        prompt=prompt,
        images=image_paths,
        options={
        'num_ctx': 32768
        },
    )
    if not response or not response.get("done"):
        raise RuntimeError(f"Ollama generate (batch) failed or incomplete: {response!r}")
    raw = (response.get("response") or "").strip()
    return parse_batch_descriptions(raw, image_paths)


def ensure_model_exists(model: str) -> None:
    if model not in SUPPORTED_MODELS.keys():
        raise ValueError(
            f"Model '{model}' is not supported. Supported models are: {list(SUPPORTED_MODELS.keys())}"
        )
    try:
        logging.getLogger(__name__).info(
            f"ImageSummary Model: checking availability -> {model}"
        )
        resp = ollama.list()
        models = [m.model for m in resp["models"]]
        if model not in models:
            logging.getLogger(__name__).info(
                f"ImageSummary Model: pulling model -> {model}"
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
    and post-process the response (strip any </think> blocks).
    """
    response = ollama.generate(
        model=model,
        prompt=IMAGE_PROMPT,
        images=[image_path],
    )
    if response and response.get("done"):
        return extract_response_after_think(response.get("response", "").strip())
    return str(response)


def describe_images_batch(
    model: str,
    image_paths: list[str],
    *,
    max_images_per_request: int | None = None,
    max_parallel_workers: int | None = None,
) -> dict[str, str]:
    """
    Describe many images via Ollama, then parse JSON into one string per path.

    For a single path, delegates to :func:`describe_image`. For multiple paths,
    splits into chunks of at most ``max_images_per_request`` images (see
    :func:`resolve_batch_chunk_size`), then runs up to ``max_parallel_workers``
    chunks concurrently via :class:`~concurrent.futures.ThreadPoolExecutor`
    (default 5; env ``IMAGE_SUMMARY_BATCH_PARALLEL_WORKERS``).

    Note: Ollama may serialize GPU work; parallel requests mainly overlap HTTP
    and server-side queuing—tune workers if you see contention or OOM.
    """
    if not image_paths:
        return {}
    if len(image_paths) == 1:
        p = image_paths[0]
        return {p: describe_image(model, p)}

    chunk_size = resolve_batch_chunk_size(max_images_per_request)
    log = logging.getLogger(__name__)
    n = len(image_paths)
    chunks: list[list[str]] = [
        image_paths[start : start + chunk_size] for start in range(0, n, chunk_size)
    ]

    if len(chunks) == 1:
        chunk = chunks[0]
        label = f"1-{len(chunk)} of {n}"
        log.info(
            "ImageSummary model: Ollama batch chunk %s (%d file(s), chunk_size=%d)",
            label,
            len(chunk),
            chunk_size,
        )
        return _describe_chunk_worker(model, chunk)

    max_workers = min(
        resolve_batch_parallel_workers(max_parallel_workers),
        len(chunks),
    )
    log.info(
        "ImageSummary model: Ollama batch %d chunk(s), up to %d parallel workers "
        "(chunk_size=%d, total files=%d)",
        len(chunks),
        max_workers,
        chunk_size,
        n,
    )
    results_by_index: dict[int, dict[str, str]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(_describe_chunk_worker, model, chunk): i
            for i, chunk in enumerate(chunks)
        }
        for fut in as_completed(future_to_index):
            idx = future_to_index[fut]
            results_by_index[idx] = fut.result()

    merged: dict[str, str] = {}
    for i in range(len(chunks)):
        merged.update(results_by_index[i])
    return merged
