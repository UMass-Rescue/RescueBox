#!/usr/bin/env python3
"""
Concurrent end-to-end test: N parallel POSTs to ``audio/transcribe`` (same input dir).

Requires a running RescueBox API (default ``http://127.0.0.1:8080``).

Environment:
  RESCUEBOX_API_BASE   Base URL including ``/api`` (default: http://127.0.0.1:8080/api)
  TRANSCRIBE_INPUT_DIR Directory containing audio files (default: demo path below)
  CONCURRENT_USERS     Number of requests (default: 5)
  TRANSCRIBE_TIMEOUT   Per-request timeout in seconds (default: 600)
  E2E_SERIAL           If ``1`` or ``true``, run requests **one after another** (same paths).
                       Use when parallel POSTs fail with 500 (shared model / GPU not safe for
                       concurrent inference in the current backend).

Example::

  poetry run python scripts/e2e_concurrent_transcribe.py
  E2E_SERIAL=1 poetry run python scripts/e2e_concurrent_transcribe.py
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from typing import Any

import httpx

DEFAULT_BASE = "http://127.0.0.1:8080/api"
DEFAULT_INPUT = "/home/tester/Documents/demo/transcribe-audio/inputs/"


def _payload(input_dir: str) -> dict[str, Any]:
    return {
        "inputs": {"input_dir": {"path": input_dir}},
        "parameters": {},
    }


async def _one_transcribe(
    client: httpx.AsyncClient,
    base: str,
    input_dir: str,
    user_index: int,
) -> tuple[int, int, float, str]:
    url = f"{base.rstrip('/')}/audio/transcribe"
    headers = {"X-RescueBox-User-Id": f"e2e-concurrent-{user_index}"}
    t0 = time.perf_counter()
    try:
        r = await client.post(url, json=_payload(input_dir), headers=headers)
        elapsed = time.perf_counter() - t0
        snippet = (r.text or "")[:400].replace("\n", " ")
        return user_index, r.status_code, elapsed, snippet
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return user_index, -1, elapsed, repr(e)


async def _run() -> int:
    base = os.environ.get("RESCUEBOX_API_BASE", DEFAULT_BASE).rstrip("/")
    input_dir = os.environ.get("TRANSCRIBE_INPUT_DIR", DEFAULT_INPUT)
    n = int(os.environ.get("CONCURRENT_USERS", "15"))
    timeout = float(os.environ.get("TRANSCRIBE_TIMEOUT", "600"))
    serial = os.environ.get("E2E_SERIAL", "").strip().lower() in ("1", "true", "yes")

    root = base[: -len("/api")] if base.endswith("/api") else base.replace("/api", "")
    liveness = f"{root}/api/probes/liveness/"
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as probe:
        try:
            lr = await probe.get(liveness)
            if lr.status_code != 200:
                print(f"Liveness check failed: GET {liveness} -> {lr.status_code}", file=sys.stderr)
                return 1
        except Exception as e:
            print(f"Server not reachable at {liveness}: {e}", file=sys.stderr)
            return 1

    mode = "serial (sequential)" if serial else "parallel (asyncio.gather)"
    print(
        f"Transcribe e2e [{mode}]: {n} POSTs -> {base}/audio/transcribe\n"
        f"  input_dir={input_dir}\n"
        f"  timeout={timeout}s each\n"
    )

    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
        if serial:
            results = []
            for i in range(n):
                results.append(await _one_transcribe(client, base, input_dir, i))
        else:
            tasks = [_one_transcribe(client, base, input_dir, i) for i in range(n)]
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
            "\nHint: If parallel runs return 500 (e.g. PyTorch size errors), the ASR model may not\n"
            "  be safe for concurrent use on this host. Retry with:  E2E_SERIAL=1",
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
