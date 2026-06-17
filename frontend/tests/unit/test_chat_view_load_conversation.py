"""Unit tests for load_conversation error handling (components.chat.view)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from frontend.components.chat.view import load_conversation

TEST_ID = "conv-load-1"


@pytest.mark.asyncio
async def test_load_conversation_navigation_error_notifies():
    mock_db = MagicMock()
    mock_conv = MagicMock()
    mock_conv.model_dump = MagicMock(return_value={})
    mock_db.get_conversation = AsyncMock(return_value=mock_conv)
    mock_db.get_messages = AsyncMock(return_value=[])

    with patch(
        "frontend.components.chat.view.get_chat_history_db", return_value=mock_db
    ), patch(
        "frontend.components.chat.view.ui.run_javascript",
        side_effect=OSError("Storage error"),
    ), patch(
        "frontend.components.chat.view.ui.notify"
    ) as mock_notify:
        await load_conversation(TEST_ID)

    mock_notify.assert_called()
    assert "Error loading conversation" in mock_notify.call_args[0][0]
    assert mock_notify.call_args[1].get("type") == "negative"
