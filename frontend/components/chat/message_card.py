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
                # If content looks like generated help/markdown (starts with "###")
                # or it's long, allow wider max width.
                if (isinstance(content, str) and content.strip().startswith('###')) or (isinstance(content, str) and len(content) > 300):
                    card_width_class = 'max-w-3xl'

            with ui.row().classes(f'w-full {alignment}'):
                with ui.card().classes(f'{bg_color} {card_width_class} shadow-sm'):
                    with ui.column().classes('p-1.5 w-full gap-1'):
                        if role == 'user':
                            ui.label('You').classes('font-medium text-xs')
                        else:
                            ui.label('🤖 Assistant').classes('font-medium text-xs')

                        if isinstance(content, str) and content.startswith('##'):
                            ui.markdown(content).classes('text-sm')
                        else:
                            ui.label(content).classes('text-sm')
                        # ui.label(timestamp).classes('text-xs opacity-70')
    except Exception as e:
        logger.exception("Error rendering message card: %s", e)
