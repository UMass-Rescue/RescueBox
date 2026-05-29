import logging
from nicegui import ui

from frontend.design_tokens import Design

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Assistant-only: global body uses 0.8rem !important on /chatbot — !text-* overrides (see guided_markdown).
ASSISTANT_MARKDOWN_CLASSES = (
    "prose prose-zinc max-w-none "
    "!text-base !leading-relaxed "
    "[&_p]:!text-base [&_li]:!text-base "
    "[&_h1]:!text-xl [&_h2]:!text-lg [&_h3]:!text-base"
)
ASSISTANT_PLAIN_CLASSES = "!text-base !leading-relaxed text-zinc-800"

# User chat is always plain text (prompts). Markdown rendering is for assistant replies only.
USER_PLAIN_CLASSES = "!text-base !leading-relaxed text-zinc-800"


def render_message_card(container: ui.element, role: str, content: str, timestamp: str) -> None:
    """
    Render a chat message card inside container.
    """
    try:
        with container:
            alignment = "items-end" if role == "user" else "items-start"
            bubble = (
                Design.CHAT_USER_BUBBLE
                if role == "user"
                else Design.CHAT_ASSISTANT_BUBBLE
            )

            card_width_class = (
                Design.CHAT_ASSISTANT_BUBBLE_WIDTH
                if role != "user"
                else "max-w-sm"
            )

            with ui.row().classes(f"w-full {alignment}"):
                with ui.card().classes(f"{bubble} {card_width_class}"):
                    with ui.column().classes("w-full gap-1"):
                        if role == "user":
                            ui.label("YOU:").classes(Design.CHAT_USER_LABEL)
                        else:
                            ui.label("Assistant").classes(
                                "font-medium !text-xs sm:!text-sm text-zinc-500 uppercase tracking-wide"
                            )

                        if isinstance(content, str) and content.startswith('##') and role != 'user':
                            ui.markdown(content).classes(ASSISTANT_MARKDOWN_CLASSES)
                        else:
                            body_cls = (
                                ASSISTANT_PLAIN_CLASSES
                                if role != 'user'
                                else USER_PLAIN_CLASSES
                            )
                            if isinstance(content, str) and '\n' in content:
                                body_cls += ' whitespace-pre-line'
                            ui.label(content).classes(body_cls)
                        # ui.label(timestamp).classes('text-xs opacity-70')
    except Exception as e:
        logger.exception("Error rendering message card: %s", e)
