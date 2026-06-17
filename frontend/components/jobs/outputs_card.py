"""Job detail outputs card (results preview, inputs summary, actions)."""

from __future__ import annotations

import logging

from nicegui import ui
from rb.api.models import ResponseBody, TaskSchema

from frontend.chatbot.config import ToolRegistry
from frontend.database.job_field_utils import (
    coerce_task_schema_and_request_body,
    compute_job_results_title,
    extract_job_fields,
)
from frontend.components.results import (
    ResultsPreview,
    augment_response_model_dump_for_image_summary,
)
from frontend.components.jobs.export import render_case_export_button
from frontend.components.jobs.forms import render_compact_inputs_summary
from frontend.components.jobs.header_actions import (
    render_error_status,
    render_job_action_buttons,
    render_job_actions,
)
from frontend.components.ui_exceptions import SCHEMA_PARSE_ERRORS, UI_RENDER_ERRORS

logger = logging.getLogger(__name__)


async def render_job_outputs_card(container, _api_client, job):
    """
    Render job outputs inside provided container. This is the extracted component
    previously inline inside `job_details.render_job_outputs`.
    """
    job_fields = extract_job_fields(job)
    job_uid = job_fields["uid"]
    response = job_fields["response"]
    status = job_fields["status"]
    status_text = job_fields["statusText"]
    task_schema_dict = job_fields["taskSchema"]
    endpoint = job_fields["endpoint"]
    endpoint_chain = job_fields.get("endpointChain")
    endpoint_name = (
        ToolRegistry.display_name_for_endpoint(endpoint) if endpoint else None
    )
    endpoint_name_chain = (
        [ToolRegistry.display_name_for_endpoint(ep) for ep in endpoint_chain]
        if isinstance(endpoint_chain, list) and endpoint_chain
        else None
    )

    logger.debug("Rendering job outputs for job: %s", job_uid)

    with container:
        if not response:
            st = str(status or "")
            if st == "Failed":
                # Message + context live on the Details tab with metadata (no duplicate red card).
                ui.label("No result output was stored for this job.").classes(
                    "text-sm font-medium text-zinc-800"
                )
                ui.label(
                    "Open the Details tab for the failure message, timestamps, "
                    "request inputs, and parameters."
                ).classes("text-sm text-zinc-600 mt-1")
                return
            logger.warning("Job has no response, showing error status: %s", status)
            render_error_status(status, status_text)
            return

        try:
            if isinstance(response, ResponseBody):
                response_body = response
            else:
                response_body = ResponseBody(**response)
        except UI_RENDER_ERRORS as e:
            logger.error("Invalid response format: %s", str(e))
            ui.label(f"Invalid response format: {str(e)}").classes("text-red-600")
            return

        with ui.card().classes(
            "w-full min-w-0 max-w-full self-stretch bg-white border border-slate-200 shadow-md rounded-2xl p-6"
        ):
            # Breadcrumbs live on the job page layout only (avoid duplicating under Outputs).

            # Header and action buttons
            with ui.row().classes("items-center justify-between mb-4"):
                try:
                    if isinstance(task_schema_dict, dict):
                        TaskSchema(**task_schema_dict)
                    task_title = compute_job_results_title(
                        endpoint_name, endpoint_name_chain
                    )
                except UI_RENDER_ERRORS:
                    task_title = (
                        task_schema_dict.get("shortTitle", "Results")
                        if isinstance(task_schema_dict, dict)
                        else "Results"
                    )

                ui.label(task_title).classes("text-2xl font-bold")
                with ui.row().classes("gap-2 items-center") as actions_row:
                    try:
                        render_job_actions(actions_row, job_fields)
                    except UI_RENDER_ERRORS:
                        render_job_action_buttons(job_fields)
                    try:
                        render_case_export_button(job_fields)
                    except UI_RENDER_ERRORS as e:
                        logger.error("CASE export button not shown: %s", e)

            # Inputs/parameters summary
            try:
                request_body_dict = job_fields.get("request", {})
                if request_body_dict and task_schema_dict:
                    task_schema, request_body = coerce_task_schema_and_request_body(
                        task_schema_dict, request_body_dict
                    )
                    render_compact_inputs_summary(
                        ui.column(), task_schema, request_body
                    )
            except SCHEMA_PARSE_ERRORS as e:
                logger.error("Could not render inputs summary: %s", str(e))

            results_container = ui.column().classes("w-full min-w-0 max-w-full gap-4")
            preview_dump = augment_response_model_dump_for_image_summary(
                response_body.model_dump(), job_fields
            )
            ResultsPreview.render(results_container, preview_dump)
