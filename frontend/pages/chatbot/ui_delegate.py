from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from frontend.pages.chatbot.state import ChatMessage


@runtime_checkable
class ChatUIDelegate(Protocol):
    """Protocol representing UI operations available to chatbot coordinators and processors."""

    def add_message(self, message: ChatMessage, scroll_after: bool = True) -> None:
        """Add a chat message to the UI."""
        ...

    async def show_error(self, message: str) -> None:
        """Display an error message to the user."""
        ...

    def update_status(
        self,
        status: str,
        scroll_after: bool = True,
        scroll_to_form: bool = False,
    ) -> None:
        """Update the status indicator in the UI."""
        ...

    async def load_form(
        self,
        endpoint: str,
        arguments: dict[str, Any],
        remaining_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        """Load and display an interactive tool form in the UI."""
        ...

    def set_input_enabled(self, enabled: bool) -> None:
        """Enable or disable the user input controls."""
        ...
