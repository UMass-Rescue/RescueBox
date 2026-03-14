import logging
from nicegui import ui
from typing import Any, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def render_tool_result_card(container: ui.element, content: str, ui_styling=None, job_id: str | None = None) -> None:
    """Render a standalone tool result card."""
    try:
        with container:
            with ui.card().classes(getattr(ui_styling, 'CARD_TOOL_RESULT', 'p-4 bg-green-50')):
                ui.label("✅ Result").classes(getattr(ui_styling, 'LABEL_TOOL_RESULT_TITLE', 'font-semibold'))
                ui.label(content).classes(getattr(ui_styling, 'LABEL_TOOL_RESULT_CONTENT', 'text-sm'))
                # Inline View Job button for this result, if job_id provided
                if job_id:
                    label = f"View Job {job_id}"
                    async def _open_job_modal(jid=job_id):
                        try:
                            from frontend.database import get_job_db
                            job_db = get_job_db()
                            job_record = await job_db.get_job_by_uid(jid)
                            with ui.dialog() as dialog:
                                with ui.card().classes(getattr(ui_styling, 'CARD_TOOL_RESULT', 'p-4 bg-green-50')):
                                    ui.label(f"Job {jid}").classes(getattr(ui_styling, 'LABEL_TOOL_RESULT_TITLE', 'font-semibold'))
                                    if job_record:
                                        ui.label(f"Status: {getattr(job_record, 'status', 'Unknown')}").classes('text-sm')
                                        ui.label(f"Model/Endpoint: {getattr(job_record, 'endpoint', 'N/A')}").classes('text-sm')
                                        ui.label(f"Start: {getattr(job_record, 'startTime', 'N/A')}").classes('text-xs text-gray-600')
                                    else:
                                        ui.label("Job details not found in local DB.").classes('text-sm text-red-600')
                                    with ui.row().classes('mt-3'):
                                        ui.button("Open Jobs Page", on_click=lambda: ui.run_javascript(f"window.open('/jobs/{jid}', '_blank')")).classes('bg-blue-600 text-white')
                                        ui.button("Close", on_click=dialog.close).classes('ml-2 bg-gray-300')
                                dialog.open()
                        except Exception as e:
                            logger.exception("Failed to open job modal: %s", e)

                    ui.button(label, on_click=_open_job_modal).classes(getattr(ui_styling, 'BUTTON_VIEW_JOB', 'ml-2 bg-blue-500 text-white'))
    except Exception as e:
        logger.exception("Error rendering tool result card: %s", e)
