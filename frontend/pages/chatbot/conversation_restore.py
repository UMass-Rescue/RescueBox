from __future__ import annotations

from nicegui import ui

from frontend.components.chat import UIOperations, render_welcome_message
from frontend.database import get_chat_history_db
from frontend.pages.chatbot.history_ui import (
    _history_record_to_chat_message,
    _is_adjacent_job_started_then_completed,
    render_merged_job_tool_results,
    render_persisted_history_message,
)
from frontend.pages.chatbot.state import ChatbotStateManager


async def restore_conversation(
    state_manager: ChatbotStateManager, chat_container, conversation_id: str
) -> None:
    """Load persisted messages into the chat UI and sync state."""
    state_manager.reset_conversation()
    chat_container.clear()
    state_manager.set_conversation_id(conversation_id)

    chat_db = get_chat_history_db()
    messages = await chat_db.get_messages(conversation_id)

    render_welcome_message(chat_container)

    with chat_container:
        ui.separator()
        ui.label("Conversation history").classes(
            "text-xs font-semibold text-slate-500 uppercase tracking-wider"
        )

    i = 0
    n = len(messages)
    while i < n:
        msg = messages[i]
        if i + 1 < n and _is_adjacent_job_started_then_completed(msg, messages[i + 1]):
            state_manager.add_message(_history_record_to_chat_message(msg))
            state_manager.add_message(_history_record_to_chat_message(messages[i + 1]))
            render_merged_job_tool_results(chat_container, msg, messages[i + 1])
            i += 2
        else:
            state_manager.add_message(_history_record_to_chat_message(msg))
            render_persisted_history_message(chat_container, msg)
            i += 1

    UIOperations.scroll_to_bottom()
    state_manager.set_status("Ready")
    state_manager.set_input_enabled(False, hide_completely=True)
