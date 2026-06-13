import json
import logging

from nicegui import ui

from frontend import utils
from frontend.components.chat.dialogs import show_conversation_view_dialog
from frontend.database import get_chat_history_db
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

from frontend.utils.ui import is_ephemeral_ui_error

logger = logging.getLogger(__name__)


def _notify_negative(message: str) -> None:
    try:
        ui.notify(message, type="negative")
    except RuntimeError:
        pass


async def view_conversation(conversation_id: str):
    """
    View full conversation in a dialog.
    """
    logger.debug("Viewing conversation: %s", conversation_id)

    chat_history = get_chat_history_db()
    conversation = await chat_history.get_conversation(conversation_id)
    messages = await chat_history.get_messages(conversation_id)

    if not conversation:
        ui.notify("Conversation not found", type="negative")
        return

    try:
        show_conversation_view_dialog(
            conversation,
            messages,
            title=conversation.title if hasattr(conversation, "title") else None,
        )
    except UI_RENDER_ERRORS as e:
        logger.error("Error in show_conversation_view_dialog: %s", e)
        # Fallback to inline dialog if component fails


async def load_conversation(conversation_id: str):
    """
    Load a conversation into the chat.
    """
    logger.debug("Loading conversation: %s", conversation_id)
    try:
        chat_history = get_chat_history_db()
        conversation = await chat_history.get_conversation(conversation_id)
        if not conversation:
            ui.notify("Conversation not found", type="negative")
            return
        messages = await chat_history.get_messages(conversation_id)
        conv_dict = (
            conversation.model_dump() if hasattr(conversation, "model_dump") else {}
        )
        messages_list = [
            m.model_dump() if hasattr(m, "model_dump") else dict(m) for m in messages
        ]
        try:
            utils.set_conversation_to_load(conversation_id, conv_dict, messages_list)
        except UI_RENDER_ERRORS as storage_exc:
            logger.warning(
                "Could not stash conversation for load fallback: %s", storage_exc
            )

        target = f"/chatbot?load_conversation={conversation_id}"
        # Full reload so /chatbot route runs again with query params (navigate.to alone may not).
        ui.run_javascript(f"window.location.assign({json.dumps(target)})")
    except UI_RENDER_ERRORS as e:
        if is_ephemeral_ui_error(e):
            logger.debug("Navigation skipped in no-client context: %s", e)
            return
        logger.error("Error loading conversation: %s", e)
        _notify_negative(f"Error loading conversation: {e}")


async def rerun_tool_call(message_id: str):
    """
    Re-run a persisted tool message.

    On the chatbot page, delegates to :func:`handle_rerun_parameter` in-process.
    Otherwise navigates to ``/chatbot?rerun=…`` so the route handler can rerun.
    """
    logger.info("Rerunning tool call: %s", message_id)
    try:
        chat_history = get_chat_history_db()
        message = await chat_history.get_tool_call_by_id(message_id)
        if not message:
            ui.notify("Tool call not found for rerun", type="negative")
            return

        from frontend.pages.chatbot.chat_page import ChatbotPage
        from frontend.pages.chatbot.routes import handle_rerun_parameter

        if ChatbotPage.get_instance() is not None:
            await handle_rerun_parameter(message_id)
            return

        endpoint = getattr(message, "tool_call_endpoint", None) or "tool"
        ui.notify(f"Re-running: {endpoint}", type="info")
        ui.navigate.to(f"/chatbot?rerun={message_id}")
    except UI_RENDER_ERRORS as e:
        logger.error("Error rerunning tool call: %s", str(e), exc_info=True)
        ui.notify(f"Error rerunning tool call: {e}", type="negative")
    except Exception as e:
        logger.exception("Unexpected error rerunning tool call %s", message_id)
        _notify_negative(f"Error rerunning tool call: {e}")
