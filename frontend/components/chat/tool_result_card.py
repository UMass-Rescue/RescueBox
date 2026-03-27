import logging
from nicegui import ui

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def render_tool_result_card(container: ui.element, content: str, ui_styling=None, job_id: str | None = None) -> None:
    """Render a standalone tool result card."""
    try:
        with container:
            with ui.card().classes(getattr(ui_styling, 'CARD_TOOL_RESULT', 'p-4 bg-green-50')):
                ui.label("✅ Result").classes(getattr(ui_styling, 'LABEL_TOOL_RESULT_TITLE', 'font-semibold'))
                ui.label(content).classes(getattr(ui_styling, 'LABEL_TOOL_RESULT_CONTENT', 'text-sm'))
                # Inline View Job — go straight to job detail page (no intermediate modal)
                if job_id:
                    label = f"View Job {job_id}"

                    def _go_to_job(jid=job_id):
                        ui.navigate.to(f"/jobs/{jid}")

                    ui.button(label, on_click=_go_to_job).classes(
                        getattr(ui_styling, 'BUTTON_VIEW_JOB', 'ml-2 bg-blue-500 text-white')
                    )
    except Exception as e:
        logger.exception("Error rendering tool result card: %s", e)
