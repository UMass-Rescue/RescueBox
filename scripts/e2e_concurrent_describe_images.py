#!/usr/bin/env python3
"""
Concurrent end-to-end test: N parallel POSTs to ``image_summary/summarize-images``.

Requires a running RescueBox API (default ``http://127.0.0.1:8080``).

Environment:
  RESCUEBOX_API_BASE      Base URL including ``/api`` (default: http://127.0.0.1:8080/api)
  DESCRIBE_INPUT_DIR      Directory containing input images (default: demo path below)
  DESCRIBE_OUTPUT_PARENT  Parent directory; each user writes to ``.../user-{i}/`` (created if missing)
  IMAGE_SUMMARY_MODEL     Ollama model id (default: gemma3:4b)
  CONCURRENT_USERS        Number of requests (default: 15)
  DESCRIBE_TIMEOUT        Per-request timeout in seconds (default: 600)
  E2E_SERIAL              If ``1`` or ``true``, run requests **one after another**.

Example::

  poetry run python scripts/e2e_concurrent_describe_images.py
  E2E_SERIAL=1 poetry run python scripts/e2e_concurrent_describe_images.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

DEFAULT_BASE = "http://127.0.0.1:8080/api"
DEFAULT_INPUT = "/home/tester/Documents/demo/describe-images/inputs"
DEFAULT_OUTPUT_PARENT = "/home/tester/Documents/demo/describe-images/outputs/e2e-concurrent"


def _payload(input_dir: str, output_dir: str, model: str) -> dict[str, Any]:
    return {
        "inputs": {
            "input_dir": {"path": input_dir},
            "output_dir": {"path": output_dir},
        },
        "parameters": {"model": model},
    }


async def _one_describe(
    client: httpx.AsyncClient,
    base: str,
    input_dir: str,
    output_dir: str,
    model: str,
    user_index: int,
) -> tuple[int, int, float, str]:
    url = f"{base.rstrip('/')}/image_summary/summarize-images"
    headers = {"X-RescueBox-User-Id": f"e2e-concurrent-{user_index}"}
    t0 = time.perf_counter()
    try:
        r = await client.post(
            url, json=_payload(input_dir, output_dir, model), headers=headers
        )
        elapsed = time.perf_counter() - t0
        snippet = (r.text or "")[:400].replace("\n", " ")
        return user_index, r.status_code, elapsed, snippet
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return user_index, -1, elapsed, repr(e)


async def _run() -> int:
    base = os.environ.get("RESCUEBOX_API_BASE", DEFAULT_BASE).rstrip("/")
    input_dir = os.environ.get("DESCRIBE_INPUT_DIR", DEFAULT_INPUT)
    out_parent = os.environ.get("DESCRIBE_OUTPUT_PARENT", DEFAULT_OUTPUT_PARENT)
    model = os.environ.get("IMAGE_SUMMARY_MODEL", "moondream:latest" )
    n = int(os.environ.get("CONCURRENT_USERS", "1"))
    timeout = float(os.environ.get("DESCRIBE_TIMEOUT", "600"))
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
    output_dirs = []
    for i in range(n):
        d = Path(out_parent) / f"user-{i}"
        d.mkdir(parents=True, exist_ok=True)
        output_dirs.append(str(d))

    mode = "serial (sequential)" if serial else "parallel (asyncio.gather)"
    print(
        f"Describe images e2e [{mode}]: {n} POSTs -> {base}/image_summary/summarize-images\n"
        f"  input_dir={input_dir}\n"
        f"  output_parent={out_parent} (user-0 .. user-{n - 1})\n"
        f"  model={model}\n"
        f"  timeout={timeout}s each\n"
    )

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        if serial:
            results = []
            for i in range(n):
                results.append(
                    await _one_describe(
                        client, base, input_dir, output_dirs[i], model, i
                    )
                )
        else:
            tasks = [
                _one_describe(client, base, input_dir, output_dirs[i], model, i)
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
            "\nHint: If parallel runs fail, try E2E_SERIAL=1 to rule out shared-model contention.",
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
