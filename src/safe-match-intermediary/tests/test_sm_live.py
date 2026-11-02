"""Check a real deployment with the smoke test's checks, in-process.

Run with RUN_INTEGRATION=1 and RESCUEBOX_SAFE_MATCH_CREDENTIALS set to a staging
credentials file. `smoketest.py --mode live` runs the same checks against a real
intermediary process or container.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import smoketest
from rb.lib.safe_match import SafeMatchClient
from safe_match_intermediary.app import create_app
from safe_match_intermediary.config import Settings

CREDENTIALS = os.getenv("RESCUEBOX_SAFE_MATCH_CREDENTIALS", "")

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1" or not CREDENTIALS,
    reason="needs RUN_INTEGRATION=1 and RESCUEBOX_SAFE_MATCH_CREDENTIALS",
)


def test_a_paraphrase_finds_its_original(tmp_path: Path) -> None:
    settings = Settings("live", "127.0.0.1", 8090, tmp_path, Path(CREDENTIALS))
    with TestClient(create_app(settings), base_url="http://127.0.0.1") as client:
        smoketest.check(SafeMatchClient(http=client), timeout=600)
