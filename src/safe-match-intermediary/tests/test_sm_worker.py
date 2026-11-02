import asyncio
import itertools

import pytest

from safe_match_intermediary.outbox import Outbox, Worker
from safe_match_intermediary.remote import RemoteError

ITEM = {
    "sha256": "a" * 64,
    "investigator_email": "x@example.org",
    "essay_version": 1,
    "essay": "a red bicycle",
}
OTHER = {**ITEM, "sha256": "b" * 64}


class Scripted:
    """Raise the scripted outcomes in order, then deliver."""

    def __init__(self, *outcomes: Exception):
        self.outcomes, self.items = list(outcomes), []

    async def upload(self, item: dict) -> None:
        self.items.append(item)
        if self.outcomes:
            raise self.outcomes.pop(0)


class Sleeps(list):
    async def __call__(self, seconds: float) -> None:
        self.append(seconds)


async def until(condition, seconds: float = 2.0) -> None:
    async with asyncio.timeout(seconds):
        while not condition():
            await asyncio.sleep(0.01)


async def test_backoff_doubles_caps_and_resets() -> None:
    outbox, sleeps = Outbox(None), Sleeps()
    worker = Worker(outbox, Scripted(*[RemoteError("unavailable")] * 10), sleeps)
    outbox.put(ITEM)
    for _ in range(11):
        await worker.step()
    assert sleeps == [1, 2, 4, 8, 16, 32, 64, 128, 256, 300]
    assert worker.backoff == 0 and outbox.counts()["pending"] == 0


async def test_retry_after_sets_the_pause() -> None:
    outbox, sleeps = Outbox(None), Sleeps()
    worker = Worker(
        outbox, Scripted(RemoteError("unavailable", retry_after=30)), sleeps
    )
    outbox.put(ITEM)
    await worker.step()
    assert sleeps == [30]


@pytest.mark.parametrize("kind", ["unauthorized", "forbidden", "unavailable"])
async def test_service_problems_keep_every_row_pending(kind: str) -> None:
    outbox = Outbox(None)
    worker = Worker(outbox, Scripted(RemoteError(kind)), Sleeps())
    outbox.put(ITEM)
    await worker.step()
    assert outbox.counts() == {"pending": 1, "failed": 0}
    assert outbox.next_due().item == ITEM


async def test_a_rejected_upload_fails_only_its_row() -> None:
    details = {
        "code": "invalid_request",
        "message": "m",
        "details": {"fields": ["essay"]},
    }
    outbox, sleeps = Outbox(None), Sleeps()
    worker = Worker(outbox, Scripted(RemoteError("rejected", 400, details)), sleeps)
    outbox.put(ITEM)
    await worker.step()
    assert outbox.db.execute("SELECT essay, error FROM outbox").fetchone() == (
        None,
        "invalid_request:essay",
    )
    assert sleeps == [] and worker.backoff == 0


async def test_a_failing_row_moves_behind_the_others() -> None:
    outbox = Outbox(None, clock=itertools.count().__next__)
    remote = Scripted(RemoteError("unavailable"))
    worker = Worker(outbox, remote, Sleeps())
    outbox.put(ITEM)
    outbox.put(OTHER)
    await worker.step()
    await worker.step()
    assert remote.items == [ITEM, OTHER]
    assert outbox.next_due().item == ITEM


async def test_an_upload_during_delivery_is_delivered_next() -> None:
    outbox = Outbox(None)
    newer = {**ITEM, "essay_version": 2, "essay": "a newer essay"}

    class Racing(Scripted):
        async def upload(self, item: dict) -> None:
            await super().upload(item)
            if len(self.items) == 1:
                outbox.put(newer)

    remote = Racing()
    worker = Worker(outbox, remote, Sleeps())
    outbox.put(ITEM)
    await worker.step()
    await worker.step()
    assert remote.items == [ITEM, newer] and outbox.counts()["pending"] == 0


async def test_an_upload_wakes_an_idle_worker() -> None:
    outbox, remote = Outbox(None), Scripted()
    worker = Worker(outbox, remote, Sleeps(), idle=60)
    task = asyncio.create_task(worker.run())
    await asyncio.sleep(0.01)
    outbox.put(ITEM)
    worker.wake.set()
    await until(lambda: remote.items == [ITEM])
    task.cancel()


async def test_cancelling_a_delivery_leaves_its_row_pending() -> None:
    class Hanging:
        async def upload(self, item: dict) -> None:
            await asyncio.Event().wait()

    outbox = Outbox(None)
    outbox.put(ITEM)
    task = asyncio.create_task(Worker(outbox, Hanging(), Sleeps()).step())
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert outbox.counts()["pending"] == 1


async def test_an_unexpected_error_does_not_stop_delivery() -> None:
    outbox, remote = Outbox(None), Scripted(RuntimeError("boom"))
    worker = Worker(outbox, remote, Sleeps(), idle=60)
    outbox.put(ITEM)
    task = asyncio.create_task(worker.run())
    await until(lambda: outbox.counts()["pending"] == 0)
    task.cancel()
    assert remote.items == [ITEM, ITEM]
