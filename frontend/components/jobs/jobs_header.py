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
                with ui.row().classes('gap-2'):
                    if on_refresh:
                        ui.button('Refresh', on_click=on_refresh).classes('mb-4 rb-brand-primary text-white')
                    else:
                        ui.button('Refresh').classes('mb-4 rb-brand-primary text-white')
    except Exception as e:
        logger.exception("Failed to render jobs header component: %s", e)
        # Fallback inline
        with container:
            with ui.row().classes('items-center justify-between mb-6'):
                ui.label(title).classes('text-4xl font-bold')
                with ui.row().classes('gap-2'):
                    ui.button('Refresh').classes('mb-4 rb-brand-primary text-white')

