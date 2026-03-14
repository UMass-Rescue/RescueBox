import logging
from nicegui import ui
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_success_header(container: ui.element, job_id: Optional[str] = None) -> None:
    """Render the standardized success header used by ResultRenderer."""
    try:
        with container:
            with ui.row().classes('items-center gap-3 mb-6'):
                ui.icon('celebration', size='2rem').classes('text-green-600')
                with ui.column():
                    ui.label('Job Completed Successfully!').classes('text-2xl font-bold text-green-800')
                    if job_id:
                        ui.label(f'Job ID: {job_id}').classes('text-sm text-green-600 font-mono')
    except Exception as e:
        logger.exception("Error rendering success header: %s", e)
