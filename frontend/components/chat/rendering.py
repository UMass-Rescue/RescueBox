import logging
from typing import Any
from .ui_bridge import ui, label, row, column, card, button, markdown
from frontend.design_tokens import Design

logger = logging.getLogger(__name__)

ASSISTANT_MARKDOWN_CLASSES = "prose prose-zinc max-w-none !text-base !leading-relaxed"
USER_PLAIN_CLASSES = "!text-base !leading-relaxed text-zinc-800"

def render_welcome_message(container: ui.element) -> None:
    with container:
        with card().classes('w-full max-w-sm bg-white ring-1 ring-zinc-200 shadow-sm rounded-2xl rounded-tl-none'):
            with column().classes('p-3 gap-1'):
                label('Assistant').classes('font-medium !text-sm text-zinc-500 uppercase tracking-wide')
                label('New conversation. How can I help you?').classes('!text-base !leading-relaxed text-zinc-800')
                with row().classes('mt-2'):
                    button('Open Tools Menu', icon='menu').props('flat dense no-caps').classes('text-sm text-zinc-600 hover:text-zinc-900').on('click', lambda: ui.run_javascript('document.querySelectorAll("button").forEach(b => { if(b.innerText.includes("Menu")) b.click(); })'))

def render_message_card(container: ui.element, role: str, content: str, timestamp: str = "") -> None:
    try:
        with container:
            alignment = "items-end" if role == "user" else "items-start"
            bubble = Design.CHAT_USER_BUBBLE if role == "user" else Design.CHAT_ASSISTANT_BUBBLE
            with row().classes(f"w-full {alignment}"):
                with card().classes(f"{bubble} max-w-2xl"):
                    if role == "user": 
                        label("YOU:").classes(Design.CHAT_USER_LABEL)
                    else:
                        label("Assistant").classes("font-medium !text-xs text-zinc-500 uppercase tracking-wide")
                    
                    if isinstance(content, str) and content.startswith('##') and role != 'user':
                        markdown(content).classes(ASSISTANT_MARKDOWN_CLASSES)
                    else:
                        label(content).classes(USER_PLAIN_CLASSES + (' whitespace-pre-line' if '\n' in str(content) else ''))
    except Exception as e:
        logger.error("Error rendering message card: %s", e)

def render_conversation_card(container: ui.column, conversation: Any, view_callback, load_callback) -> None:
    with container:
        with card().classes('p-4 cursor-pointer hover:bg-zinc-50'):
            with row().classes('items-center justify-between mb-2'):
                label(conversation.title).classes('font-semibold flex-1')
            with row().classes('gap-2'):
                button('View', on_click=lambda: view_callback(conversation.conversation_id)).classes('text-sm rb-brand-primary text-white')
                button('Load', on_click=lambda: load_callback(conversation.conversation_id)).classes('text-sm rb-brand-primary text-white')

def render_message_in_dialog(message: Any) -> None:
    """Simplified version for dialog viewing."""
    role = getattr(message, 'role', 'assistant')
    content = getattr(message, 'content', '')
    with column().classes('w-full border-b border-zinc-100 pb-2 mb-2'):
        label(role.upper()).classes('text-xs font-bold text-zinc-400')
        label(content).classes('text-sm text-zinc-800 whitespace-pre-wrap')
