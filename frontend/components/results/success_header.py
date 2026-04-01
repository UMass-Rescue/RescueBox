import logging
from nicegui import ui
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_success_header(
    container: ui.element,
    job_id: Optional[str] = None,
    *,
    pipeline_intermediate: bool = False,
    pipeline_completed_step: Optional[int] = None,
    pipeline_total_steps: Optional[int] = None,
) -> None:
    """Render the standardized success header used by ResultRenderer."""
    try:
        with container:
            with ui.row().classes('items-center gap-3 mb-6'):
                ui.icon('celebration', size='2rem').classes('text-green-600')
                with ui.column():
                    if pipeline_intermediate and pipeline_completed_step and pipeline_total_steps:
                        ui.label('Job complete').classes('text-2xl font-bold text-green-800')
                        ui.label(
                            f'Step {pipeline_completed_step} of {pipeline_total_steps} finished'
                        ).classes('text-sm text-green-700')
                    else:
                        ui.label('Job Completed Successfully!').classes('text-2xl font-bold text-green-800')
                    if job_id:
                        ui.label(f'Job ID: {job_id}').classes('text-sm text-green-600 font-mono')
    except Exception as e:
        logger.exception("Error rendering success header: %s", e)
