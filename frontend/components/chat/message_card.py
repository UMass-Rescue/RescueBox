import logging
from nicegui import ui

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Assistant-only: global body uses 0.8rem !important on /chatbot — !text-* overrides (see guided_markdown).
ASSISTANT_MARKDOWN_CLASSES = (
    'prose prose-slate max-w-none '
    '!text-base !leading-relaxed '
    '[&_p]:!text-base [&_li]:!text-base '
    '[&_h1]:!text-xl [&_h2]:!text-lg [&_h3]:!text-base'
)
ASSISTANT_PLAIN_CLASSES = '!text-base !leading-relaxed'

# User chat is always plain text (prompts). Markdown rendering is for assistant replies only.
USER_PLAIN_CLASSES = '!text-base !leading-relaxed text-white'


def render_message_card(container: ui.element, role: str, content: str, timestamp: str) -> None:
    """
    Render a chat message card inside container.
    """
    try:
        with container:
            alignment = 'items-end' if role == 'user' else 'items-start'
            bg_color = 'bg-blue-600 text-white' if role == 'user' else 'bg-gray-200'

            # Make long or help-style assistant messages wider so help text and
            # multi-line markdown can use more horizontal space.
            card_width_class = 'max-w-sm'
            if role != 'user':
                # If content looks like generated help/markdown (starts with "###"),
                # is long, or has line breaks (e.g. multi-step pipeline list), allow wider max width.
                if (
                    (isinstance(content, str) and content.strip().startswith('###'))
                    or (isinstance(content, str) and len(content) > 300)
                    or (isinstance(content, str) and '\n' in content)
                ):
                    card_width_class = 'max-w-3xl'

            with ui.row().classes(f'w-full {alignment}'):
                with ui.card().classes(f'{bg_color} {card_width_class} shadow-sm'):
                    with ui.column().classes('p-1.5 w-full gap-1'):
                        if role == 'user':
                            ui.label('YOU:').classes('font-semibold !text-sm sm:!text-base text-white')
                        else:
                            ui.label('🤖 Assistant').classes('font-medium !text-sm sm:!text-base')

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
