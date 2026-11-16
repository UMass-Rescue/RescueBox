"""Job page UI adapters — delegates to ``frontend.components.jobs``."""

import logging

from nicegui import ui

from frontend.components import jobs as job_ui

from .utils import get_plugin_name

logger = logging.getLogger(__name__)

render_job_action_buttons = job_ui.render_job_action_buttons
render_error_status = job_ui.render_error_status
render_job_metadata = job_ui.render_job_metadata
render_model_info = job_ui.render_model_info


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
    "get_plugin_name",
    "render_compact_inputs_summary",
    "render_error_status",
    "render_job_action_buttons",
    "render_job_details_panel",
    "render_job_metadata",
    "render_job_outputs_card",
    "render_model_info",
    "render_readonly_form",
]
