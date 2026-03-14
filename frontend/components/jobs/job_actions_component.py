import logging
from nicegui import ui
from typing import Any, Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_job_actions(container: ui.element, job_fields: Dict[str, Any]) -> None:
    """
    Render job action buttons into the provided container.
    Delegates to the existing job actions implementation with a safe fallback.
    """
    try:
        from frontend.pages.jobs.components.job_actions import render_job_action_buttons
        with container:
            render_job_action_buttons(job_fields)
    except Exception as e:
        logger.exception("Failed to render job actions via component: %s", e)
        # Fallback minimal actions
        with container:
            ui.button('Inspect', on_click=lambda: None).classes('bg-blue-600 text-white')
            ui.button('Run', on_click=lambda: None).classes('bg-green-600 text-white')

