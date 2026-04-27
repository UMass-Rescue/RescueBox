"""Helpers for NiceGUI chatbot page integration tests (reduce flakes from slow render)."""

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nicegui.testing import User


async def open_chatbot_and_wait_for_ready(user: "User", *, max_wait_s: float = 30.0) -> None:
    """Open /chatbot and wait until primary controls are in the DOM."""
    await user.open("/chatbot")
    # Async page render (ChatbotPage.render) can lag behind user.open in long test runs
    await asyncio.sleep(0.6)
    step = 0.25
    n = max(1, int(max_wait_s / step))
    for _ in range(n):
        try:
            await user.should_see("Send")
            return
        except AssertionError:
            await asyncio.sleep(step)
    await user.should_see("Send")


def find_chat_textarea(user: "User"):
    """Resolve the main chat textarea by label or placeholder substring."""
    for needle in (
        "Type your request",
        "Type in a rescuebox",
        "rescuebox task",
    ):
        try:
            return user.find(needle)
        except AssertionError:
            continue
    raise AssertionError("Chat textarea not found (tried label/placeholder substrings)")


async def assert_chatbot_header_visible(user: "User") -> None:
    """Header shows RescueBox Assistant and/or Assistant depending on layout."""
    try:
        await user.should_see("RescueBox Assistant")
    except AssertionError:
        await user.should_see("Assistant")
