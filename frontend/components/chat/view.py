import json
import logging
from nicegui import ui

import frontend.utils as utils
from frontend.database import get_chat_history_db

logger = logging.getLogger(__name__)


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
        from .dialogs import show_conversation_view_dialog

        show_conversation_view_dialog(
            conversation,
            messages,
            title=conversation.title if hasattr(conversation, "title") else None,
        )
    except Exception as e:
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
        except Exception as storage_exc:
            logger.warning(
                "Could not stash conversation for load fallback: %s", storage_exc
            )

        target = f"/chatbot?load_conversation={conversation_id}"
        # Full reload so /chatbot route runs again with query params (navigate.to alone may not).
        ui.run_javascript(f"window.location.assign({json.dumps(target)})")
    except RuntimeError as ui_error:
        if (
            "slot" in str(ui_error).lower()
            or "cannot be determined" in str(ui_error).lower()
        ):
            logger.debug("Navigation skipped in no-client context: %s", ui_error)
        else:
            raise
    except Exception as e:
        logger.error("Error loading conversation: %s", e)
        try:
            ui.notify(f"Error loading conversation: {e}", type="negative")
        except RuntimeError:
            pass


async def rerun_tool_call(message_id: str):
    """
    Rerun a tool call by navigating to chatbot with rerun parameter.
    """
    logger.debug("Rerunning tool call: %s", message_id)
    try:
        from frontend.database import get_chat_history_db

        chat_history = get_chat_history_db()
        message = await chat_history.get_tool_call_by_id(message_id)
        if not message:
            ui.notify("Tool call not found for rerun", type="negative")
            return
        # Show what we're rerunning for test compatibility
        endpoint = getattr(message, "tool_call_endpoint", "tool")
        ui.notify(f"Re-running: {endpoint}", type="info")
        ui.navigate.to(f"/chatbot?rerun={message_id}")
    except Exception as e:
        logger.error("Error rerunning tool call: %s", str(e))
        ui.notify(f"Error rerunning tool call: {e}", type="negative")
