import logging
from nicegui import ui

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
                            ui.label('YOU:').classes('font-medium text-xs')
                        else:
                            ui.label('🤖 Assistant').classes('font-medium text-xs')

                        if isinstance(content, str) and content.startswith('##'):
                            ui.markdown(content).classes('text-sm')
                        else:
                            body_cls = 'text-sm'
                            if isinstance(content, str) and '\n' in content:
                                body_cls += ' whitespace-pre-line'
                            ui.label(content).classes(body_cls)
                        # ui.label(timestamp).classes('text-xs opacity-70')
    except Exception as e:
        logger.exception("Error rendering message card: %s", e)
