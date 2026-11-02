"""Check a real deployment through the intermediary, like semantic-match-api's smoke test.

Run with RUN_INTEGRATION=1 and RESCUEBOX_SAFE_MATCH_CREDENTIALS set to a staging
credentials file. Fixed synthetic hashes get a new essay version on every run, so
repeated runs do not grow the corpus.
"""

import hashlib
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rb.lib.safe_match import SafeMatchClient
from safe_match_intermediary.app import create_app
from safe_match_intermediary.config import Settings

CREDENTIALS = os.getenv("RESCUEBOX_SAFE_MATCH_CREDENTIALS", "")
ESSAYS = {
    "original": "A red bicycle leans against a brick wall beside a wooden door.",
    "unrelated": "A bowl of oranges sits on a kitchen table under a window.",
}
PARAPHRASE = "A red bike rests against a brick wall next to a door."

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1" or not CREDENTIALS,
    reason="needs RUN_INTEGRATION=1 and RESCUEBOX_SAFE_MATCH_CREDENTIALS",
)


def synthetic_sha256(label: str) -> str:
    return hashlib.sha256(f"semantic-match-smoketest/{label}".encode()).hexdigest()


def ranks_original_first(sdk: SafeMatchClient) -> bool:
    order = [match["sha256"] for match in sdk.query(PARAPHRASE)["matches"]]
    original, unrelated = synthetic_sha256("original"), synthetic_sha256("unrelated")
    return original in order and (
        unrelated not in order or order.index(original) < order.index(unrelated)
    )


def test_a_paraphrase_finds_its_original(tmp_path: Path) -> None:
    settings = Settings("live", "127.0.0.1", 8090, tmp_path, Path(CREDENTIALS))
    with TestClient(create_app(settings), base_url="http://127.0.0.1") as client:
        sdk = SafeMatchClient(http=client)
        version = int(time.time())
        for label, essay in ESSAYS.items():
            sdk.upload(
                sha256=synthetic_sha256(label),
                investigator_email="smoketest@example.org",
                essay_version=version,
                essay=essay,
                file_name=f"smoketest-{label}.txt",
            )
        deadline = time.monotonic() + 600
        while not ranks_original_first(sdk):
            assert time.monotonic() < deadline, "the original was not found in time"
            time.sleep(5)
        assert sdk.status()["remote"] == "ok"
