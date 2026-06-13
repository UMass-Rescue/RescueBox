"""Job page UI adapters — delegates to ``frontend.components.jobs``."""

import logging
from datetime import datetime

from nicegui import ui

from frontend.components import jobs as job_ui
from frontend.utils.logging import (
    format_audit_trail_markdown,
    generate_audit_trail_for_job,
)
from frontend.utils.ui import notify_error, notify_info, notify_success

from .utils import get_plugin_name
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

_AUDIT_BTN = (
    "bg-slate-100 hover:bg-slate-200 text-slate-800 px-4 py-2 rounded-lg "
    "font-medium transition-colors border border-slate-200"
)

logger = logging.getLogger(__name__)

render_job_action_buttons = job_ui.render_job_action_buttons
render_error_status = job_ui.render_error_status
render_job_metadata = job_ui.render_job_metadata
render_model_info = job_ui.render_model_info


async def create_audit_trail_button(job_id: str):
    async def export_audit():
        try:
            notify_info("Generating audit trail...")
            audit_trail = await generate_audit_trail_for_job(job_id)
            if "error" in audit_trail:
                notify_error(f"Error: {audit_trail['error']}")
                return

            markdown_content = format_audit_trail_markdown(audit_trail)
            filename = f"audit_trail_job_{job_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            ui.download(markdown_content.encode("utf-8"), filename=filename)
            notify_success(f"Audit trail exported: {filename}")
        except UI_RENDER_ERRORS as e:
            logger.error("Error exporting audit trail: %s", e)
            notify_error(f"Error exporting audit trail: {str(e)}")

    return ui.button(
        "Export Audit Trail",
        color=None,
        on_click=export_audit,
    ).classes(_AUDIT_BTN)


def render_compact_inputs_summary(task_schema, request_body):
    job_ui.render_compact_inputs_summary(ui.column(), task_schema, request_body)


def render_readonly_form(task_schema, request_body):
    job_ui.render_readonly_form(
        ui.column().classes("w-full min-w-0"), task_schema, request_body
    )


async def render_job_outputs_card(container, api_client, job):
    await job_ui.render_job_outputs_card(container, api_client, job)


async def render_job_details_panel(container, api_client, job_fields):
    await job_ui.render_job_details_panel(container, api_client, job_fields)


# Re-export for callers that import get_plugin_name from this module historically.
__all__ = [
    "create_audit_trail_button",
    "render_job_action_buttons",
    "render_compact_inputs_summary",
    "render_readonly_form",
    "render_error_status",
    "render_model_info",
    "render_job_metadata",
    "render_job_outputs_card",
    "render_job_details_panel",
    "get_plugin_name",
]
