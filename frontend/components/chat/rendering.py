import logging
from typing import Any
from .ui_bridge import ui, label, row, column, card, button, markdown
from frontend.design_tokens import Design
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)

ASSISTANT_MARKDOWN_CLASSES = "prose prose-slate max-w-none !text-base !leading-relaxed"
USER_PLAIN_CLASSES = "!text-base !leading-relaxed text-slate-800"

_WELCOME_CARD_CLS = (
    "w-full max-w-sm bg-white ring-1 ring-slate-200 shadow-sm rounded-2xl "
    "rounded-tl-none border-l-4 border-l-[#881c1c]"
)
_OPEN_TOOLS_MENU_JS = (
    'document.querySelectorAll("button").forEach(b => { '
    'if(b.innerText.includes("Menu")) b.click(); })'
)


def render_welcome_message(container: ui.element) -> None:
    with container:
        with card().classes(_WELCOME_CARD_CLS):
            with column().classes("p-3 gap-1"):
                label("Assistant").classes(
                    "font-medium !text-sm text-slate-500 uppercase tracking-wider"
                )
                label("New conversation. How can I help you?").classes(
                    "!text-base !leading-relaxed text-slate-800"
                )


def render_message_card(
    container: ui.element, role: str, content: str, _timestamp: str = ""
) -> None:
    try:
        with container:
            alignment = "items-end" if role == "user" else "items-start"
            bubble = (
                Design.CHAT_USER_BUBBLE
                if role == "user"
                else Design.CHAT_ASSISTANT_BUBBLE
            )
            with row().classes(f"w-full {alignment}"):
                with card().classes(f"{bubble} max-w-4xl"):
                    if role == "user":
                        label("YOU:").classes(Design.CHAT_USER_LABEL)
                    else:
                        label("Assistant").classes(
                            "font-semibold !text-sm text-slate-500 uppercase tracking-wider"
                        )

                    if (
                        isinstance(content, str)
                        and content.startswith("##")
                        and role != "user"
                    ):
                        markdown(content).classes(ASSISTANT_MARKDOWN_CLASSES)
                    else:
                        label(content).classes(
                            USER_PLAIN_CLASSES
                            + (" whitespace-pre-line" if "\n" in str(content) else "")
                        )
    except UI_RENDER_ERRORS as e:
        logger.error("Error rendering message card: %s", e)


def render_conversation_card(
    container: ui.column, conversation: Any, view_callback, load_callback
) -> None:
    with container:
        with card().classes(
            "p-4 cursor-pointer hover:bg-slate-50 border border-slate-200 rounded-xl shadow-sm transition-all"
        ):
            with row().classes("items-center justify-between mb-2"):
                label(conversation.title).classes("font-semibold flex-1 text-slate-800")
            with row().classes("gap-2"):
                button(
                    "View",
                    color=None,
                    on_click=lambda: view_callback(conversation.conversation_id),
                ).classes(
                    "text-sm bg-slate-100 hover:bg-slate-200 text-slate-800 px-3 py-1 rounded transition-colors"
                )
                button(
                    "Load",
                    color=None,
                    on_click=lambda: load_callback(conversation.conversation_id),
                ).classes(
                    "text-sm rb-brand-primary text-white px-3 py-1 rounded transition-colors"
                )


def render_message_in_dialog(message: Any) -> None:
    """Simplified version for dialog viewing."""
    role = getattr(message, "role", "assistant")
    content = getattr(message, "content", "")
    with column().classes("w-full border-b border-slate-100 pb-2 mb-2"):
        label(role.upper()).classes(
            "text-xs font-bold text-slate-400 uppercase tracking-wider"
        )
        label(content).classes("text-sm text-slate-800 whitespace-pre-wrap")
