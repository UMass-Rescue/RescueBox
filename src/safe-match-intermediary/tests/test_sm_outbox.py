import random
import stat
import sys
from pathlib import Path

import pytest

from safe_match_intermediary.outbox import Outbox
from safe_match_intermediary.stub import FakeApi


def item(
    sha: str = "a", email: str = "x@e.org", version: int = 1, name: str | None = None
) -> dict:
    """Same file and version always get the same essay, as one pipeline would write."""
    body = {"sha256": sha * 64, "investigator_email": email, "essay_version": version}
    body["essay"] = f"essay of {sha} at version {version}"
    return {**body, "file_name": name} if name else body


def snapshot(api: FakeApi) -> tuple[dict, dict]:
    names = {
        (sha256, email): row.get("file_name")
        for sha256, rows in api.investigators.items()
        for email, row in rows.items()
    }
    return dict(api.essays), names


def test_coalescing_matches_delivering_every_upload_in_order() -> None:
    rng = random.Random(7)
    for _ in range(300):
        sequential, coalesced, outbox = FakeApi(), FakeApi(), Outbox(None)
        for _ in range(rng.randint(1, 8)):
            upload = item(
                rng.choice("ab"),
                rng.choice(["x@e.org", "y@e.org"]),
                rng.randint(1, 3),
                rng.choice([None, "p.jpg", "q.jpg"]),
            )
            sequential.upload(upload)
            outbox.put(upload)
        while (row := outbox.next_due()) is not None:
            coalesced.upload(row.item)
            outbox.delivered(row)
        assert snapshot(coalesced) == snapshot(sequential)


def test_an_equal_version_keeps_the_first_essay_like_the_api() -> None:
    outbox = Outbox(None)
    outbox.put(item())
    outbox.put({**item(), "essay": "another essay at the same version"})
    assert outbox.next_due().item == item()


def test_writes_apply_only_to_the_generation_read() -> None:
    outbox = Outbox(None)
    outbox.put(item(version=1))
    row = outbox.next_due()
    outbox.put(item(version=2))
    outbox.delivered(row)
    outbox.rejected(row, "invalid_request")
    outbox.deferred(row)
    assert outbox.next_due().item == item(version=2)
    assert outbox.counts() == {"pending": 1, "failed": 0}


def test_a_rejected_row_keeps_no_essay_until_uploaded_again() -> None:
    outbox = Outbox(None)
    outbox.put(item(version=2))
    outbox.rejected(outbox.next_due(), "invalid_request:essay")
    row = outbox.db.execute("SELECT essay, error FROM outbox").fetchone()
    assert row == (None, "invalid_request:essay")
    assert outbox.counts() == {"pending": 0, "failed": 1}
    outbox.put(item(version=1))
    assert outbox.next_due().item == item(version=1)


def test_pending_rows_survive_reopening(tmp_path: Path) -> None:
    first = Outbox(tmp_path / "outbox.db")
    first.put(item(name="p.jpg"))
    first.close()
    assert Outbox(tmp_path / "outbox.db").next_due().item == item(name="p.jpg")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions")
def test_the_database_is_private(tmp_path: Path) -> None:
    path = tmp_path / "data" / "outbox.db"
    Outbox(path).close()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
