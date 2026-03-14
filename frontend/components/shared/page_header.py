import logging
from nicegui import ui
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_page_header(title: str, actions_callable: Optional[callable] = None):
    """Render a standardized page header with title and optional action buttons area."""
    with ui.row().classes('items-center justify-between w-full mb-6'):
        ui.label(title).classes('text-4xl font-bold')
        with ui.row().classes('gap-2'):
            if actions_callable:
                try:
                    actions_callable()
                except Exception as e:
                    logger.exception("Error rendering header actions: %s", e)
            else:
                # default placeholder
                ui.label('')

