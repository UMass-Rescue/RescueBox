import json
from typing import Optional, Callable, List, Any

from nicegui import ui

from frontend.components.chat.rendering import render_conversation_card
from frontend.database import get_chat_history_db
from frontend.design_tokens import Design


def show_help_dialog(help_text: str, title: Optional[str] = "RescueBox Help") -> None:
    with ui.dialog() as dialog, ui.card().classes(Design.PANEL_SHELL_CARD_WIDE):
        with ui.row().classes(Design.PANEL_SHELL_HEADER):
            ui.label(title or "Help").classes(Design.PANEL_SHELL_HEADER_TITLE)
            ui.button(color=None, on_click=dialog.close).props("flat round dense")
        with ui.column().classes("w-full flex-1 overflow-y-auto p-6"):
            ui.markdown(help_text or "No help available.")
    dialog.open()


async def show_history_dialog(
    on_conversation_select: Callable[[str], None]
) -> ui.dialog:
    chat_db = get_chat_history_db()
    conversations = await chat_db.get_all_conversations()

    with ui.dialog() as dialog, ui.card().classes(Design.PANEL_SHELL_CARD_WIDE):
        with ui.row().classes(Design.PANEL_SHELL_HEADER):
            ui.label("Chat History").classes(Design.PANEL_SHELL_HEADER_TITLE)
            ui.button(color=None, on_click=dialog.close).props("flat round dense")

        with ui.column().classes(
            f"{Design.PANEL_SHELL_BODY} gap-3 overflow-y-auto max-h-[60vh] w-full"
        ):
            if not conversations:
                ui.label("No chat history found.").classes("text-zinc-500 italic p-4")
            else:
                for conv in conversations:
                    # view_callback shows a view dialog, load_callback loads into the main chat
                    async def do_load(cid=conv.conversation_id):
                        await on_conversation_select(cid)
                        dialog.close()

                    async def do_view(cid=conv.conversation_id, ctitle=conv.title):
                        msgs = await chat_db.get_messages(cid)
                        show_conversation_view_dialog(None, msgs, title=ctitle)

                    render_conversation_card(
                        ui.column().classes("w-full"),
                        conv,
                        view_callback=do_view,
                        load_callback=do_load,
                    )
    dialog.open()
    return dialog


def show_conversation_view_dialog(
    _conversation: Any, messages: List[Any], title: str = None
):
    """Render persisted messages; include JSON for tool calls and job payloads when present."""

    def _render_message_card(msg: Any) -> None:
        role = getattr(msg, "role", "?")
        content = getattr(msg, "content", "") or ""
        with ui.card().classes(
            "w-full p-3 bg-zinc-50 border border-zinc-200 rounded-lg"
        ):
            ui.label(f"{role}: {content}").classes(
                "text-sm font-medium text-zinc-900 break-words w-full min-w-0"
            )

            extras: List[tuple[str, str]] = []

            args = getattr(msg, "tool_call_arguments", None)
            if isinstance(args, dict) and (
                args.get("inputs") is not None or args.get("parameters") is not None
            ):
                extras.append(
                    (
                        "Job inputs & parameters",
                        json.dumps(args, indent=2, default=str),
                    )
                )

            tcalls = getattr(msg, "tool_calls", None)
            if isinstance(tcalls, list) and tcalls:
                extras.append(("Tool calls", json.dumps(tcalls, indent=2, default=str)))

            for expansion_title, body in extras:
                with ui.expansion(expansion_title).classes("w-full mt-2"):
                    ui.code(body).classes(
                        "text-xs w-full whitespace-pre-wrap break-all"
                    )

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-4xl max-h-[80vh]"):
        ui.label(f"Conversation: {title or 'View'}").classes("text-2xl font-bold mb-4")
        with ui.column().classes(
            "space-y-3 overflow-y-auto max-h-[65vh] w-full min-w-0"
        ):
            for msg in messages:
                _render_message_card(msg)
        ui.button("Close", color=None, on_click=dialog.close).classes(
            Design.BTN_MEDIUM_GRAY
        )
    dialog.open()
