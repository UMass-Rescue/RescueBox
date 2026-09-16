#!/usr/bin/env python3
"""
Concurrent end-to-end test: N parallel POSTs to ``image_embeddings/search_images``.

Mirrors the flow in ``frontend/demo/image_search_walkthrough.md``: CLIP embed + rank images
under a folder by text query.

Requires a running RescueBox API (default ``http://127.0.0.1:8080``).

Environment:
  RESCUEBOX_API_BASE       Base URL including ``/api`` (default: http://127.0.0.1:8080/api)
  IMAGE_SEARCH_INPUT_DIR   Directory of images to search (default: demo path below)
  IMAGE_SEARCH_QUERY       Natural-language query string (default: sports or games)
  IMAGE_SEARCH_CLIP_MODEL  HF CLIP id (default: openai/clip-vit-large-patch14-336, same as plugin)
  IMAGE_SEARCH_TOP_K       Top results to return (default: 5, walkthrough “top-5” style)
  IMAGE_SEARCH_MIN_SIM     Minimum similarity threshold 0–1 (default: 0.13)
  CONCURRENT_USERS         Number of parallel requests (default: 10)
  IMAGE_SEARCH_TIMEOUT     Per-request timeout in seconds (default: 600)
  E2E_SERIAL               If ``1`` or ``true``, run requests **one after another**.

Example::

  poetry run python scripts/e2e_concurrent_image_search.py
  CONCURRENT_USERS=10 poetry run python scripts/e2e_concurrent_image_search.py
  E2E_SERIAL=1 poetry run python scripts/e2e_concurrent_image_search.py
"""

from __future__ import annotations

import asyncio
import os
import random
import sys
import time
from typing import Any

import httpx

DEFAULT_BASE = "http://127.0.0.1:8080/api"
# Walkthrough: ``search-images`` → ``inputs`` (see demo_files_explorer preset ``image_search``).
DEFAULT_INPUT = "/home/tester/Documents/demo/search-images/inputs"
DEFAULT_CLIP_MODEL = "openai/clip-vit-large-patch14-336"


_DEFAULT_QUERY_OPTIONS = (
    "sports or games",
    "food",
    "kid",
    "a small child",
    "computer",
)
DEFAULT_QUERY = "sports or games"


def _payload(
    input_dir: str,
    query: str,
    model_name: str,
    top_k: int,
    min_similarity: float,
) -> dict[str, Any]:
    return {
        "inputs": {
            "input_dir": {"path": input_dir},
            "query": {"text": query},
        },
        "parameters": {
            "model_name": model_name,
            "top_k": top_k,
            "min_similarity": min_similarity,
        },
    }


async def _one_search(
    client: httpx.AsyncClient,
    base: str,
    input_dir: str,
    query: str,
    model_name: str,
    top_k: int,
    min_similarity: float,
    user_index: int,
) -> tuple[int, int, float, str]:
    url = f"{base.rstrip('/')}/image_embeddings/search_images"
    headers = {"X-RescueBox-User-Id": f"e2e-image-search-{user_index}"}
    t0 = time.perf_counter()
    try:
        r = await client.post(
            url,
            json=_payload(input_dir, query, model_name, top_k, min_similarity),
            headers=headers,
        )
        elapsed = time.perf_counter() - t0
        snippet = (r.text or "")[:400].replace("\n", " ")
        return user_index, r.status_code, elapsed, snippet
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return user_index, -1, elapsed, repr(e)


async def _run() -> int:
    base = os.environ.get("RESCUEBOX_API_BASE", DEFAULT_BASE).rstrip("/")
    input_dir = os.environ.get("IMAGE_SEARCH_INPUT_DIR", DEFAULT_INPUT)
    model_name = os.environ.get("IMAGE_SEARCH_CLIP_MODEL", DEFAULT_CLIP_MODEL)
    top_k = int(os.environ.get("IMAGE_SEARCH_TOP_K", "5"))
    min_similarity = float(os.environ.get("IMAGE_SEARCH_MIN_SIM", "0.13"))
    n = int(os.environ.get("CONCURRENT_USERS", "40"))
    timeout = float(os.environ.get("IMAGE_SEARCH_TIMEOUT", "600"))
    serial = os.environ.get("E2E_SERIAL", "").strip().lower() in ("1", "true", "yes")

    root = base[: -len("/api")] if base.endswith("/api") else base.replace("/api", "")
    liveness = f"{root}/api/probes/liveness/"
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as probe:
        try:
            lr = await probe.get(liveness)
            if lr.status_code != 200:
                print(
                    f"Liveness check failed: GET {liveness} -> {lr.status_code}",
                    file=sys.stderr,
                )
                return 1
        except Exception as e:
            print(f"Server not reachable at {liveness}: {e}", file=sys.stderr)
            return 1

    mode = "serial (sequential)" if serial else "parallel (asyncio.gather)"
    query = random.choice(_DEFAULT_QUERY_OPTIONS)
    print(
        f"Image search e2e [{mode}]: {n} POSTs -> {base}/image_embeddings/search_images\n"
        f"  input_dir={input_dir}\n"
        f"  query={query!r}\n"
        f"  model_name={model_name}\n"
        f"  top_k={top_k}  min_similarity={min_similarity}\n"
        f"  timeout={timeout}s each\n"
    )

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        if serial:
            results = []
            for i in range(n):
                results.append(
                    await _one_search(
                        client,
                        base,
                        input_dir,
                        query,
                        model_name,
                        top_k,
                        min_similarity,
                        i,
                    )
                )
        else:
            tasks = [
                _one_search(
                    client,
                    base,
                    input_dir,
                    random.choice(_DEFAULT_QUERY_OPTIONS),
                    model_name,
                    top_k,
                    min_similarity,
                    i,
                )
                for i in range(n)
            ]
            results = await asyncio.gather(*tasks)

    ok = 0
    for idx, status, elapsed, snippet in sorted(results, key=lambda x: x[0]):
        line = f"  user {idx}: status={status} time={elapsed:.2f}s"
        if status == 200:
            ok += 1
            print(f"{line} OK")
        else:
            print(f"{line}\n    body: {snippet[:300]}...")

    print(f"\nSummary: {ok}/{n} returned HTTP 200")
    if ok < n and not serial:
        print(
            "\nHint: Parallel CLIP runs can contend for GPU/RAM; try E2E_SERIAL=1 or lower "
            "CONCURRENT_USERS if you see 500s or CUDA OOM.",
            file=sys.stderr,
        )
    return 0 if ok == n else 1


def main() -> None:
    try:
        raise SystemExit(asyncio.run(_run()))
    except KeyboardInterrupt:
        raise SystemExit(130)


if __name__ == "__main__":
    main()
