#!/usr/bin/env python3
"""
Concurrent end-to-end test: N parallel POSTs to ``/image_series_similarity/search_series``.

Tests the Image Series Similarity ML plugin on demo images in ``src-tauri/demo/image-similarity/inputs_kh``.

Requires a running RescueBox API (default ``http://127.0.0.1:8000``).

Environment:
  RESCUEBOX_API_BASE             Base URL (default: http://127.0.0.1:8000)
  IMAGE_SIMILARITY_INPUT_DIR     Directory of images to search (default: src-tauri/demo/image-similarity/inputs_kh)
  IMAGE_SIMILARITY_QUERY_IMAGE   Path to query image (default: first .jpg/.png in input_dir)
  IMAGE_SIMILARITY_MODEL         ONNX vision model (default: google/siglip2-so400m-patch14-384)
  IMAGE_SIMILARITY_TOP_K         Top results to return (default: 5)
  IMAGE_SIMILARITY_MIN_SIM       Minimum similarity threshold (default: 0.5)
  IMAGE_SIMILARITY_SCORING_MODE  Scoring mode: combined|semantic|pdq (default: combined)
  IMAGE_SIMILARITY_USER_EMAIL    User attribution email (default: e2e-tester@example.com)
  IMAGE_SIMILARITY_ANONYMIZED    Enable anonymized table search yes/no (default: no)
  CONCURRENT_USERS               Number of parallel requests (default: 10)
  IMAGE_SIMILARITY_TIMEOUT       Per-request timeout in seconds (default: 600)
  E2E_SERIAL                     If ``1`` or ``true``, run requests sequentially.

Example:
  poetry run python frontend/tests/scripts/e2e_concurrent_image_similarity.py
  CONCURRENT_USERS=5 poetry run python frontend/tests/scripts/e2e_concurrent_image_similarity.py
  E2E_SERIAL=1 poetry run python frontend/tests/scripts/e2e_concurrent_image_similarity.py
"""

from __future__ import annotations

import asyncio
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

import httpx

# Ensure UTF-8 stdout encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_BASE = "http://127.0.0.1:8000"
DEFAULT_DEMO_DIR = (
    Path(__file__).resolve().parents[3]
    / "src-tauri"
    / "demo"
    / "image-similarity"
    / "inputs_kh"
)
DEFAULT_MODEL = "google/siglip2-so400m-patch14-384"
DEFAULT_USER_EMAIL = "e2e-tester@example.com"


def _payload(
    input_dir: str,
    query_image: str,
    model_name: str,
    top_k: int,
    min_similarity: float,
    scoring_mode: str,
    user_email: str,
    enable_anonymized: str,
) -> dict[str, Any]:
    return {
        "inputs": {
            "input_dir": {"path": input_dir},
            "query_image": {"path": query_image},
        },
        "parameters": {
            "model_name": model_name,
            "top_k": top_k,
            "min_similarity": min_similarity,
            "scoring_mode": scoring_mode,
            "user_email": user_email,
            "enable_anonymized": enable_anonymized,
        },
    }


async def _one_search(
    client: httpx.AsyncClient,
    base_url: str,
    input_dir: str,
    query_image: str,
    model_name: str,
    top_k: int,
    min_similarity: float,
    scoring_mode: str,
    user_email: str,
    enable_anonymized: str,
    user_index: int,
) -> tuple[int, int, float, str]:
    clean_base = base_url.rstrip("/")
    if clean_base.endswith("/api"):
        clean_base = clean_base[:-4]
    url = f"{clean_base}/image_series_similarity/search_series"

    headers = {"X-RescueBox-User-Id": f"e2e-image-similarity-{user_index}"}
    t0 = time.perf_counter()
    try:
        r = await client.post(
            url,
            json=_payload(
                input_dir,
                query_image,
                model_name,
                top_k,
                min_similarity,
                scoring_mode,
                user_email,
                enable_anonymized,
            ),
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
    input_dir = str(
        Path(
            os.environ.get("IMAGE_SIMILARITY_INPUT_DIR", str(DEFAULT_DEMO_DIR))
        ).resolve()
    )

    query_img_env = os.environ.get("IMAGE_SIMILARITY_QUERY_IMAGE", "")
    if query_img_env:
        query_image = str(Path(query_img_env).resolve())
    else:
        p_dir = Path(input_dir)
        imgs = (
            list(p_dir.glob("*.jpg"))
            + list(p_dir.glob("*.jpeg"))
            + list(p_dir.glob("*.png"))
            + list(p_dir.glob("*.JPG"))
        )
        if not imgs:
            print(f"Error: No image files found in {input_dir}", file=sys.stderr)
            return 1
        query_image = str(imgs[0].resolve())

    model_name = os.environ.get("IMAGE_SIMILARITY_MODEL", DEFAULT_MODEL)
    top_k = int(os.environ.get("IMAGE_SIMILARITY_TOP_K", "5"))
    min_similarity = float(os.environ.get("IMAGE_SIMILARITY_MIN_SIM", "0.5"))
    scoring_mode = os.environ.get("IMAGE_SIMILARITY_SCORING_MODE", "combined")
    user_email = os.environ.get("IMAGE_SIMILARITY_USER_EMAIL", DEFAULT_USER_EMAIL)
    enable_anonymized = os.environ.get("IMAGE_SIMILARITY_ANONYMIZED", "no")

    n = int(os.environ.get("CONCURRENT_USERS", "10"))
    timeout = float(os.environ.get("IMAGE_SIMILARITY_TIMEOUT", "600"))
    serial = os.environ.get("E2E_SERIAL", "").strip().lower() in ("1", "true", "yes")

    probe_base = base[:-4] if base.endswith("/api") else base
    liveness_url = f"{probe_base}/probes/liveness/"
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as probe:
        try:
            lr = await probe.get(liveness_url)
            if lr.status_code != 200:
                print(
                    f"Liveness check failed: GET {liveness_url} -> {lr.status_code}",
                    file=sys.stderr,
                )
                return 1
        except Exception as e:
            print(f"Server not reachable at {liveness_url}: {e}", file=sys.stderr)
            return 1

    mode = "serial (sequential)" if serial else "parallel (asyncio.gather)"
    print(
        f"Image Series Similarity e2e [{mode}]: {n} POSTs -> {probe_base}/image_series_similarity/search_series\n"
        f"  input_dir={input_dir}\n"
        f"  query_image={query_image}\n"
        f"  model_name={model_name}\n"
        f"  scoring_mode={scoring_mode}\n"
        f"  top_k={top_k}  min_similarity={min_similarity}\n"
        f"  user_email={user_email}\n"
        f"  timeout={timeout}s each\n"
    )

    p_dir = Path(input_dir)
    available_imgs = (
        list(p_dir.glob("*.jpg"))
        + list(p_dir.glob("*.jpeg"))
        + list(p_dir.glob("*.png"))
        + list(p_dir.glob("*.JPG"))
    )

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        if serial:
            results = []
            for i in range(n):
                q_img = (
                    str(random.choice(available_imgs).resolve())
                    if available_imgs
                    else query_image
                )
                results.append(
                    await _one_search(
                        client,
                        base,
                        input_dir,
                        q_img,
                        model_name,
                        top_k,
                        min_similarity,
                        scoring_mode,
                        user_email,
                        enable_anonymized,
                        i,
                    )
                )
        else:
            tasks = [
                _one_search(
                    client,
                    base,
                    input_dir,
                    (
                        str(random.choice(available_imgs).resolve())
                        if available_imgs
                        else query_image
                    ),
                    model_name,
                    top_k,
                    min_similarity,
                    scoring_mode,
                    user_email,
                    enable_anonymized,
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
            "\nHint: Parallel vision model runs can contend for GPU/RAM or DB connections; "
            "try E2E_SERIAL=1 or lower CONCURRENT_USERS if you see 500s or timeouts.",
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
