#!/usr/bin/env python3
"""
Concurrent end-to-end test: age/gender predict → metadata filter → image summarize.

Mirrors the chatbot pipeline: ``POST .../age-gender/predict``, apply the same metadata
filter the UI would use, then ``POST .../image_summary/summarize-images`` with
``file_filter`` set to the matched image paths.

Requires a running RescueBox API (default ``http://127.0.0.1:8080``).

Environment:
  RESCUEBOX_API_BASE        Base URL including ``/api`` (default: http://127.0.0.1:8080/api)
  AGE_GENDER_INPUT_DIR      Image directory for classifier (default: demo path below)
  PIPELINE_OUTPUT_PARENT    Parent dir; each user uses ``.../user-{i}/`` for summarize output
  PIPELINE_METADATA_FILTER  Comma-separated filter (see ``apply_metadata_filter`` in
                            ``frontend/chatbot/multi_tool_handler.py``). Default matches the
                            walkthrough style "Male and under 10": ``Gender=Male, Age<10``.
                            (A literal ``gender=Male, age,10`` is not parseable as criteria;
                            use ``Gender=Male, Age<10`` or ``Gender=Male, Age=6`` etc.)
  IMAGE_SUMMARY_MODEL       Ollama model for describe-images (default: gemma3:4b)
  CONCURRENT_USERS          Number of parallel pipelines (default: 5)
  PIPELINE_TIMEOUT          Per-request HTTP timeout in seconds (default: 600)
  E2E_SERIAL                If ``1`` or ``true``, run pipelines one after another.

Example::

  poetry run python scripts/e2e_concurrent_age_gender_summarize.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import httpx

# Reuse the same filter semantics as the chatbot pipeline UI.
from frontend.chatbot.multi_tool_handler import (
    apply_metadata_filter,
    extract_batch_file_items,
)

DEFAULT_BASE = "http://127.0.0.1:8080/api"
DEFAULT_INPUT = "/home/tester/Documents/demo/age-gender-classifier/inputs"
DEFAULT_OUTPUT_PARENT = (
    "/home/tester/Documents/demo/age-gender-classifier/outputs/e2e-pipeline-concurrent"
)
# Walkthrough-style: male faces with age (upper bound of bracket) under 10.
DEFAULT_METADATA_FILTER = "Gender=Male, Age<10"


def _summarize_payload(
    input_dir: str,
    output_dir: str,
    model: str,
    filtered_paths: list[str],
) -> dict[str, Any]:
    inputs: dict[str, Any] = {
        "input_dir": {"path": input_dir},
        "output_dir": {"path": output_dir},
    }
    if filtered_paths:
        inputs["file_filter"] = {"files": [{"path": p} for p in filtered_paths]}
    return {
        "inputs": inputs,
        "parameters": {"model": model},
    }


async def _one_pipeline(
    client: httpx.AsyncClient,
    base: str,
    input_dir: str,
    output_dir: str,
    criteria: str,
    model: str,
    user_index: int,
) -> tuple[int, str, int, float, str]:
    """
    Returns (user_index, stage, http_status, elapsed_total_seconds, detail).
    stage is ``predict`` or ``summarize`` if failed mid-way, else ``ok``.
    """
    headers = {"X-RescueBox-User-Id": f"e2e-pipeline-{user_index}"}
    t0 = time.perf_counter()

    try:
        pr = await client.post(
            f"{base.rstrip('/')}/age-gender/predict",
            json={"inputs": {"image_directory": {"path": input_dir}}},
            headers=headers,
        )
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return user_index, "predict", -1, elapsed, repr(e)

    if pr.status_code != 200:
        elapsed = time.perf_counter() - t0
        snippet = (pr.text or "")[:400].replace("\n", " ")
        return user_index, "predict", pr.status_code, elapsed, snippet

    items = extract_batch_file_items(pr.json())
    filtered_paths = apply_metadata_filter(items, criteria)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    try:
        sr = await client.post(
            f"{base.rstrip('/')}/image_summary/summarize-images",
            json=_summarize_payload(input_dir, output_dir, model, filtered_paths),
            headers=headers,
        )
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return user_index, "summarize", -1, elapsed, repr(e)

    elapsed = time.perf_counter() - t0
    snippet = (sr.text or "")[:400].replace("\n", " ")
    return user_index, "ok", sr.status_code, elapsed, snippet


async def _run() -> int:
    base = os.environ.get("RESCUEBOX_API_BASE", DEFAULT_BASE).rstrip("/")
    input_dir = os.environ.get("AGE_GENDER_INPUT_DIR", DEFAULT_INPUT)
    out_parent = os.environ.get("PIPELINE_OUTPUT_PARENT", DEFAULT_OUTPUT_PARENT)
    criteria = os.environ.get("PIPELINE_METADATA_FILTER", DEFAULT_METADATA_FILTER)
    model = os.environ.get("IMAGE_SUMMARY_MODEL", "gemma3:1b")
    n = int(os.environ.get("CONCURRENT_USERS", "15"))
    timeout = float(os.environ.get("PIPELINE_TIMEOUT", "600"))
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

    Path(out_parent).mkdir(parents=True, exist_ok=True)
    output_dirs = [str(Path(out_parent) / f"user-{i}") for i in range(n)]

    mode = "serial (sequential)" if serial else "parallel (asyncio.gather)"
    print(
        f"Age-gender → filter → summarize e2e [{mode}]: {n} pipelines\n"
        f"  (prompt concept: detect age/gender of faces, then summarize filtered faces)\n"
        f"  input_dir={input_dir}\n"
        f"  metadata_filter={criteria!r}\n"
        f"  output_parent={out_parent} (user-0 .. user-{n - 1})\n"
        f"  model={model}\n"
        f"  timeout={timeout}s per HTTP call\n"
    )

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        if serial:
            results = []
            for i in range(n):
                results.append(
                    await _one_pipeline(
                        client, base, input_dir, output_dirs[i], criteria, model, i
                    )
                )
        else:
            tasks = [
                _one_pipeline(
                    client, base, input_dir, output_dirs[i], criteria, model, i
                )
                for i in range(n)
            ]
            results = await asyncio.gather(*tasks)

    ok = 0
    for idx, stage, status, elapsed, snippet in sorted(results, key=lambda x: x[0]):
        line = f"  user {idx}: stage={stage} status={status} time={elapsed:.2f}s"
        if stage == "ok" and status == 200:
            ok += 1
            print(f"{line} OK")
        else:
            print(f"{line}\n    body: {snippet[:320]}...")

    print(f"\nSummary: {ok}/{n} pipelines completed (predict + summarize) with HTTP 200")
    if ok < n and not serial:
        print(
            "\nHint: Retry with E2E_SERIAL=1 if parallel runs contend on GPU/Ollama.",
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
