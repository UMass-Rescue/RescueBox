import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from frontend.pages.chatbot.pickers import AnalysisPicker, ToolPicker


@pytest.mark.asyncio
async def test_tool_picker_select_tool_returns_future_result():
    container = MagicMock()
    tool_registry = MagicMock()
    picker = ToolPicker(container, tool_registry)
    picker.show = AsyncMock()

    async def simulate_click():
        await asyncio.sleep(0.01)
        picker._handle_select("detect/objects", {"arg": "val"})

    asyncio.create_task(simulate_click())
    endpoint, args = await picker.select_tool()

    assert endpoint == "detect/objects"
    assert args == {"arg": "val"}
    picker.show.assert_awaited_once()


@pytest.mark.asyncio
async def test_analysis_picker_select_analysis_returns_future_result():
    container = MagicMock()
    picker = AnalysisPicker(container)
    picker.show = AsyncMock()

    async def simulate_click():
        await asyncio.sleep(0.01)
        picker._handle_select("Deep Forensic")

    asyncio.create_task(simulate_click())
    selected = await picker.select_analysis()

    assert selected == "Deep Forensic"
    picker.show.assert_awaited_once()


@pytest.mark.asyncio
async def test_ui_flow_show_pickers_awaitable():
    from frontend.pages.chatbot.ui_flow import show_analysis_picker, show_tool_picker

    container = MagicMock()
    tool_registry = MagicMock()

    with (
        pytest.MonkeyPatch.context() as mp,
    ):
        mock_tool_picker = MagicMock()
        mock_tool_picker.select_tool = AsyncMock(return_value=("ocr/text", {"box": 1}))
        mp.setattr(
            "frontend.pages.chatbot.ui_flow.ToolPicker",
            MagicMock(return_value=mock_tool_picker),
        )

        res = await show_tool_picker(container, tool_registry)
        assert res == ("ocr/text", {"box": 1})
        mock_tool_picker.select_tool.assert_awaited_once()

        mock_analysis_picker = MagicMock()
        mock_analysis_picker.select_analysis = AsyncMock(return_value="Surface Scan")
        mp.setattr(
            "frontend.pages.chatbot.ui_flow.AnalysisPicker",
            MagicMock(return_value=mock_analysis_picker),
        )

        analysis = await show_analysis_picker(container)
        assert analysis == "Surface Scan"
        mock_analysis_picker.select_analysis.assert_awaited_once()


@pytest.mark.asyncio
async def test_show_history_dialog_future_selection():
    from frontend.components.chat.dialogs import show_history_dialog

    fake_conv = MagicMock()
    fake_conv.conversation_id = "conv-123"
    fake_conv.title = "Test Conversation"

    chat_db_mock = MagicMock()
    chat_db_mock.get_all_conversations = AsyncMock(return_value=[fake_conv])

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "frontend.components.chat.dialogs.get_chat_history_db",
            lambda: chat_db_mock,
        )

        dialog_mock = MagicMock()
        mp.setattr("frontend.components.chat.dialogs.ui.dialog", MagicMock(return_value=dialog_mock))
        card_mock = MagicMock()
        mp.setattr("frontend.components.chat.dialogs.ui.card", MagicMock(return_value=card_mock))
        mp.setattr("frontend.components.chat.dialogs.ui.row", MagicMock())
        mp.setattr("frontend.components.chat.dialogs.ui.column", MagicMock())
        mp.setattr("frontend.components.chat.dialogs.ui.label", MagicMock())
        mp.setattr("frontend.components.chat.dialogs.ui.button", MagicMock())

        captured_load_callback = []

        def fake_render_card(container, conv, view_callback, load_callback):
            captured_load_callback.append(load_callback)

        mp.setattr(
            "frontend.components.chat.dialogs.render_conversation_card",
            fake_render_card,
        )

        async def trigger_select():
            await asyncio.sleep(0.01)
            assert captured_load_callback
            await captured_load_callback[0]("conv-123")

        asyncio.create_task(trigger_select())
        result = await show_history_dialog()
        assert result == "conv-123"

