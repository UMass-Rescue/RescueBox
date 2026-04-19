import logging
from nicegui import ui
from typing import Callable, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_jobs_header(container: ui.element, title: str, on_refresh: Optional[Callable] = None):
    """
    Render the jobs page header with title and refresh button.
    """
    try:
        with container:
            with ui.row().classes('items-center justify-between mb-6'):
                ui.label(title).classes('text-4xl font-bold')
    except Exception as e:
        logger.exception("Failed to render jobs header component: %s", e)

