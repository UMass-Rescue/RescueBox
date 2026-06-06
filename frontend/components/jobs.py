from __future__ import annotations

from typing import Any, Dict, Callable, Optional
from nicegui import ui
from frontend.design_tokens import Design
from rb.api.models import TaskSchema, RequestBody, ResponseBody
from frontend.components.results import ResultsPreview
from frontend.components.results import (
    augment_response_model_dump_for_image_summary,
)
from frontend.chatbot.config import ToolRegistry
from datetime import datetime

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

"""One-click export of a completed job as CASE-style JSON-LD."""


def render_case_export_button(job_fields: Dict[str, Any]) -> None:
    """
    Add a button that downloads ``job-{uid}.jsonld`` built from the current job record.

    Only meaningful when status is completed and the job dict is available.
    """
    uid = job_fields.get("uid") or ""
    status = str(job_fields.get("status", "")).lower()

    if status != "completed" or not uid:
        return

    def _download() -> None:
        try:
            from case_export.persist import build_jsonld_bytes_from_job_dict

            data = build_jsonld_bytes_from_job_dict(job_fields)
            ui.download(data, f"rescuebox-job-{uid}.jsonld")
        except Exception as e:
            logger.exception("CASE export failed: %s", e)
            ui.notify(
                f"Export failed: {e}", type="negative", classes="rb-notify-505759"
            )

    ui.button(
        "Export CASE JSON-LD",
        icon="download",
        color=None,
        on_click=_download,
    ).classes(Design.BTN_MEDIUM_GRAY).props("dense").tooltip(
        "Download a JSON-LD fragment (UCO-oriented) for this job"
    )


def render_compact_inputs_summary(
    container: ui.element, task_schema: Any, request_body: Any
) -> None:
    """
    Render a compact summary of inputs and parameters inside `container`.
    """
    logger.debug("Rendering compact inputs summary (component)")
    with container:
        with ui.expansion("View inputs & parameters", icon="description").classes(
            "w-full mb-4"
        ):
            with ui.column().classes("gap-3 p-4 bg-zinc-50 rounded"):
                # Inputs
                if getattr(task_schema, "inputs", None):
                    ui.label("Inputs").classes("font-semibold text-lg")
                    for input_schema in task_schema.inputs:
                        field_id = input_schema.key
                        field_input = request_body.inputs.get(field_id)

                        with ui.row().classes("items-start gap-2"):
                            ui.label(input_schema.label).classes(
                                "w-32 font-semibold text-sm"
                            )

                            if field_input:
                                input_root = (
                                    field_input.root
                                    if hasattr(field_input, "root")
                                    else field_input
                                )

                                if hasattr(input_root, "path"):
                                    path_str = str(input_root.path)
                                    display_path = (
                                        path_str
                                        if len(path_str) < 80
                                        else path_str[:77] + "..."
                                    )
                                    ui.label(display_path).classes(
                                        "flex-1 text-sm font-mono text-zinc-700"
                                    )
                                elif hasattr(input_root, "text"):
                                    text = input_root.text
                                    first_line = (
                                        text.split("\n")[0] if "\n" in text else text
                                    )
                                    display_text = (
                                        first_line
                                        if len(first_line) < 100
                                        else first_line[:97] + "..."
                                    )
                                    ui.label(display_text).classes(
                                        "flex-1 text-sm text-zinc-700"
                                    )
                                else:
                                    ui.label(str(input_root)).classes(
                                        "flex-1 text-sm text-zinc-700"
                                    )
                            else:
                                ui.label("(not provided)").classes(
                                    "flex-1 text-sm text-zinc-400 italic"
                                )

                # Parameters
                if getattr(task_schema, "parameters", None):
                    ui.label("Parameters").classes("font-semibold text-lg mt-2")
                    for param_schema in task_schema.parameters:
                        param_id = param_schema.key
                        param_value = request_body.parameters.get(param_id)

                        with ui.row().classes("items-center gap-2"):
                            ui.label(param_schema.label).classes(
                                "w-32 font-semibold text-sm"
                            )
                            ui.label(
                                str(param_value)
                                if param_value is not None
                                else "(not provided)"
                            ).classes("flex-1 text-sm text-zinc-700")

    logger.debug("Compact inputs summary (component) rendered")


def render_jobs_header(
    container: ui.element, title: str, on_refresh: Optional[Callable] = None
):
    """
    Render the jobs page header with title and refresh button.
    """
    try:
        with container:
            with ui.row().classes("items-center justify-between mb-6"):
                ui.label(title).classes("text-4xl font-bold")
    except Exception as e:
        logger.exception("Failed to render jobs header component: %s", e)


def render_job_actions(container: ui.element, job_fields: Dict[str, Any]) -> None:
    """
    Render job action buttons into the provided container.
    Delegates to the existing job actions implementation with a safe fallback.
    """
    try:
        from frontend.pages.jobs import render_job_action_buttons

        with container:
            render_job_action_buttons(job_fields)
    except Exception as e:
        logger.exception("Failed to render job actions via component: %s", e)


async def render_job_details_panel(
    container: ui.element, api_client, job_fields: dict
) -> None:
    """
    Render the job details panel: metadata, model info, case notes, and read-only form.
    """
    from frontend.pages.jobs import (
        render_job_metadata,
        render_model_info,
        render_readonly_form,
    )

    request_body_dict = job_fields.get("request", {})
    task_schema_dict = job_fields.get("taskSchema")
    case_notes = job_fields.get("caseNotes")
    pipeline_filter = job_fields.get("pipelineMetadataFilterCriteria")

    with container:
        with ui.card().classes(
            "w-full min-w-0 max-w-full self-stretch bg-white border border-slate-200 shadow-md rounded-2xl p-6"
        ):
            # Job metadata header
            with ui.column().classes("gap-4 w-full min-w-0 max-w-full"):
                ui.label("Job Information").classes("text-2xl font-bold")

                # Classifier metadata filter (age/gender pipeline → next step), if recorded
                if pipeline_filter is not None:
                    with ui.column().classes("gap-2"):
                        ui.label("Classifier filter (next pipeline step)").classes(
                            "font-semibold text-zinc-700"
                        )
                        _txt = (pipeline_filter or "").strip()
                        ui.label(
                            _txt
                            if _txt
                            else "No age/gender filter — all images were eligible for the next step."
                        ).classes(
                            "text-sm text-zinc-800 whitespace-pre-wrap rounded p-3 "
                            "bg-amber-50/80 border border-amber-100"
                        )

                # Case notes section
                if case_notes:
                    with ui.column().classes("gap-2"):
                        ui.label("Case Notes").classes("font-semibold text-zinc-700")
                        ui.label(case_notes).classes(
                            "text-zinc-800 whitespace-pre-wrap rounded p-3 bg-zinc-50 border border-zinc-200"
                        )
                elif case_notes is not None and case_notes == "":
                    pass  # Empty notes, don't show section
                # If caseNotes key not present (older jobs), don't show

                # Basic info
                render_job_metadata(job_fields)

                # Model info (async)
                try:
                    await render_model_info(api_client, job_fields)
                except Exception as e:
                    logger.error("Failed to render model info: %s", e)

                # Failed runs: keep the message with other job fields (not only under Outputs).
                _status = str(job_fields.get("status") or "")
                _status_text = (job_fields.get("statusText") or "").strip()
                if _status == "Failed":
                    with ui.column().classes("gap-2 w-full min-w-0"):
                        ui.label("Failure message").classes(
                            "font-semibold text-zinc-800"
                        )
                        if _status_text:
                            ui.label(_status_text).classes(
                                "text-sm text-zinc-900 whitespace-pre-wrap rounded p-3 "
                                "bg-zinc-50 border border-zinc-200"
                            )
                        else:
                            ui.label(
                                "No error message was recorded for this run."
                            ).classes("text-sm text-zinc-600 italic")

                # Request body (read-only form)
                if task_schema_dict:
                    try:
                        task_schema = (
                            TaskSchema(**task_schema_dict)
                            if isinstance(task_schema_dict, dict)
                            else task_schema_dict
                        )
                        request_body = (
                            RequestBody(**request_body_dict)
                            if isinstance(request_body_dict, dict)
                            else request_body_dict
                        )
                        render_readonly_form(task_schema, request_body)
                    except Exception as e:
                        logger.error(
                            "Error parsing schema in details panel: %s", str(e)
                        )
                        ui.label(f"Error parsing schema: {str(e)}").classes(
                            "text-red-600"
                        )


async def render_job_outputs_card(container, api_client, job):
    """
    Render job outputs inside provided container. This is the extracted component
    previously inline inside `job_details.render_job_outputs`.
    """
    from frontend.pages.jobs import extract_job_fields, compute_job_results_title
    from frontend.pages.jobs import (
        render_error_status,
        render_job_action_buttons,
        render_compact_inputs_summary,
    )

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
        except Exception as e:
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
                except Exception:
                    task_title = (
                        task_schema_dict.get("shortTitle", "Results")
                        if isinstance(task_schema_dict, dict)
                        else "Results"
                    )

                ui.label(task_title).classes("text-2xl font-bold")
                with ui.row().classes("gap-2 items-center") as actions_row:
                    try:
                        from frontend.components.jobs import (
                            render_job_actions,
                        )

                        render_job_actions(actions_row, job_fields)
                    except Exception:
                        render_job_action_buttons(job_fields)
                    try:
                        from frontend.components.jobs import (
                            render_case_export_button,
                        )

                        render_case_export_button(job_fields)
                    except Exception as e:
                        logger.error("CASE export button not shown: %s", e)

            # Inputs/parameters summary
            try:
                request_body_dict = job_fields.get("request", {})
                if request_body_dict and task_schema_dict:
                    task_schema = (
                        TaskSchema(**task_schema_dict)
                        if isinstance(task_schema_dict, dict)
                        else task_schema_dict
                    )
                    request_body = (
                        RequestBody(**request_body_dict)
                        if isinstance(request_body_dict, dict)
                        else request_body_dict
                    )
                    render_compact_inputs_summary(task_schema, request_body)
            except Exception as e:
                logger.error("Could not render inputs summary: %s", str(e))

            results_container = ui.column().classes("w-full min-w-0 max-w-full gap-4")
            preview_dump = augment_response_model_dump_for_image_summary(
                response_body.model_dump(), job_fields
            )
            ResultsPreview.render(results_container, preview_dump)


"""
Job Row Component

This module provides the render_job_row function for displaying job information
in a table row format. The row shows job status, timestamps, and action buttons.
"""


def render_job_row(
    container,
    job: Dict,
    plugin_name: Optional[str] = None,
    on_view: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
):
    """
    Render a job row in table format.

    This function creates a table row component displaying job information including
    model name, status, timestamps, and action buttons. The row uses color-coding
    to indicate job status (Running, Completed, Failed, Canceled).

    """
    logger.debug(
        "Rendering job row for job: %s (Status: %s)",
        job.get("uid", "Unknown"),
        job.get("status", "Unknown"),
    )

    status = job.get("status", "Unknown")

    # Status Pill Badges
    status_pill_classes = {
        "Completed": "bg-emerald-50 text-emerald-700 border border-emerald-200",
        "Running": "bg-rose-50 text-[#881c1c] border border-rose-200",
        "Failed": "bg-rose-50 text-rose-700 border border-rose-200",
        "Canceled": "bg-slate-100 text-slate-600 border border-slate-200",
    }
    pill_cls = status_pill_classes.get(
        status, "bg-slate-50 text-slate-500 border border-slate-200"
    )

    # Format timestamps
    start_time_str = "N/A"
    if job.get("startTime"):
        try:
            start_time = datetime.fromisoformat(job["startTime"].replace("Z", "+00:00"))
            start_time_str = start_time.strftime("%Y-%m-%d %H:%M")
        except Exception as e:
            logger.warning(
                "Failed to parse start time: %s, error: %s", job["startTime"], e
            )
            start_time_str = job["startTime"]

    end_time_str = "N/A"
    if job.get("endTime"):
        try:
            end_time = datetime.fromisoformat(job["endTime"].replace("Z", "+00:00"))
            end_time_str = end_time.strftime("%Y-%m-%d %H:%M")
        except Exception as e:
            logger.warning("Failed to parse end time: %s, error: %s", job["endTime"], e)
            end_time_str = job["endTime"]

    job_uid = job.get("uid", "N/A")
    with container:
        with ui.row().classes(
            "p-4 border-b border-slate-200 hover:bg-slate-50 items-center w-full flex-nowrap gap-2 bg-white"
        ):
            # Job ID - truncated with ellipsis, full ID on hover
            with ui.element("div").classes("w-40 min-w-0 shrink-0"):
                id_label = ui.label(job_uid).classes(
                    "font-mono text-sm truncate block text-slate-800"
                )
                id_label.tooltip(job_uid)

            # Model name (and notes indicator)
            with ui.element("div").classes(
                "flex-1 min-w-0 overflow-hidden flex items-center gap-2 text-slate-800"
            ):
                ui.label(plugin_name or "Unknown").classes("truncate block font-medium")
                if job.get("caseNotes"):
                    notes_preview = (job["caseNotes"] or "")[:50]
                    if len(job.get("caseNotes", "") or "") > 50:
                        notes_preview += "…"
                    ui.icon("description", size="sm").classes(
                        "text-slate-500 shrink-0"
                    ).tooltip(notes_preview)

            # Times (start / end)
            with ui.column().classes("w-64 shrink-0 gap-0.5"):
                ui.label(start_time_str).classes("text-sm text-slate-700")
                ui.label(
                    f"Ended: {end_time_str}" if end_time_str != "N/A" else "Active"
                ).classes("text-xs text-slate-500")

            # Status Pill Badge
            with ui.row().classes(
                f"w-32 shrink-0 items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold {pill_cls}"
            ):
                if status == "Completed":
                    ui.icon("check_circle", size="14px")
                elif status == "Running":
                    ui.spinner(size="14px").classes("text-[#881c1c]")
                elif status == "Failed":
                    ui.icon("error", size="14px")
                else:
                    ui.icon("cancel", size="14px")
                ui.label(status)

            # Actions
            with ui.row().classes("gap-2 w-48 shrink-0 flex-nowrap"):
                if on_view:
                    ui.button(
                        "View",
                        icon="visibility",
                        color=None,
                        on_click=lambda: on_view(job["uid"]) if on_view else None,
                    ).classes(Design.BTN_PRIMARY_TIGHT)

                if status == "Running" and on_cancel:
                    ui.button(
                        "Cancel",
                        icon="cancel",
                        color=None,
                        on_click=lambda: on_cancel(job["uid"]) if on_cancel else None,
                    ).classes(
                        "bg-rose-50 hover:bg-rose-100 text-rose-700 px-3 py-1 rounded text-sm transition-colors border border-rose-200"
                    )
                elif status != "Running" and on_delete:
                    ui.button(
                        "Delete",
                        icon="delete",
                        color=None,
                        on_click=lambda: on_delete(job["uid"]) if on_delete else None,
                    ).classes(
                        "bg-rose-50 hover:bg-rose-100 text-[#881c1c] px-3 py-1 rounded text-sm transition-colors border border-rose-200"
                    )
                    # logger.debug("Delete button added")


"""Compact pipeline stepper for the job detail page."""


def short_endpoint_label(endpoint: Optional[str]) -> str:
    if not endpoint:
        return "?"
    parts = [p for p in endpoint.strip().split("/") if p]
    return (parts[-1] if parts else endpoint)[:28]


def render_pipeline_run_banner(
    *,
    root_job_id: str,
    current_job_id: str,
    steps: list[dict[str, str]],
) -> None:
    """
    Render a single-row stepper: Pipeline · run link · 1. step → 2. step …

    ``steps`` items: ``{"job_id": str, "endpoint": str}`` in pipeline order.
    """
    if len(steps) < 2:
        return
    with ui.row().classes(
        "w-full flex-wrap items-center gap-x-1 gap-y-2 mb-4 px-3 py-2 rounded-lg "
        "bg-[#505759] border border-[#3d4442]"
    ):
        ui.label("Pipeline").classes(
            "text-xs font-semibold uppercase tracking-wide text-white shrink-0"
        )
        ui.link(
            f"Run {root_job_id[:11]}…",
            f"/jobs/{root_job_id}",
        ).classes(
            "text-xs font-mono text-white/90 hover:underline shrink-0"
        ).tooltip(root_job_id)
        ui.label("·").classes("text-white/50 shrink-0")
        for i, step in enumerate(steps):
            if i:
                ui.icon("chevron_right", size="xs").classes("text-white/55 shrink-0")
            ep = short_endpoint_label(step.get("endpoint"))
            jid = (step.get("job_id") or "").strip()
            label = f"{i + 1}. {ep}"
            if jid == current_job_id:
                ui.label(label).classes(
                    "text-sm font-semibold text-white shrink-0"
                ).tooltip(jid)
            else:
                ui.link(label, f"/jobs/{jid}").classes(
                    "text-sm text-white/90 hover:underline shrink-0"
                ).tooltip(jid)


def _readonly_value_block(value: str, *, monospace: bool = False) -> None:
    """Full-width read-only field that wraps long lines (paths, text) instead of horizontal scroll."""
    extra = "font-mono text-xs" if monospace else "text-sm"
    ui.textarea(
        label="",
        value=value,
    ).classes(
        f"w-full min-w-0 max-w-full {extra} break-all"
    ).props("readonly outlined dense autogrow")


def render_readonly_form(
    container: ui.element, task_schema: Any, request_body: Any
) -> None:
    """
    Render read-only form for job inputs and parameters inside `container`.

    Uses full container width with stacked label + wrapping textarea so long paths
    do not require horizontal scrolling in a narrow input.
    """
    logger.debug("Rendering read-only form (component)")
    with container:
        ui.label("Request Inputs and Parameters").classes("text-xl font-bold mt-6")

        with ui.column().classes("gap-4 mt-4 w-full min-w-0 max-w-full"):
            # Inputs
            if getattr(task_schema, "inputs", None):
                ui.label("Inputs").classes("font-semibold text-lg")
                for input_schema in task_schema.inputs:
                    field_id = input_schema.key
                    field_input = request_body.inputs.get(field_id)

                    with ui.column().classes("w-full min-w-0 max-w-full gap-1"):
                        ui.label(input_schema.label).classes(
                            "font-semibold text-sm text-zinc-800"
                        )

                        if field_input:
                            input_root = (
                                field_input.root
                                if hasattr(field_input, "root")
                                else field_input
                            )

                            if hasattr(input_root, "path"):
                                _readonly_value_block(
                                    str(input_root.path), monospace=True
                                )
                            elif hasattr(input_root, "text"):
                                ui.textarea(
                                    label="",
                                    value=input_root.text,
                                ).classes(
                                    "w-full min-w-0 max-w-full text-sm break-words whitespace-pre-wrap"
                                ).props("readonly outlined dense autogrow")
                            else:
                                _readonly_value_block(str(input_root), monospace=True)
                        else:
                            ui.label("(not provided)").classes(
                                "text-sm text-zinc-400 italic"
                            )

            # Parameters
            if getattr(task_schema, "parameters", None):
                ui.label("Parameters").classes("font-semibold text-lg mt-4")
                for param_schema in task_schema.parameters:
                    param_id = param_schema.key
                    param_value = request_body.parameters.get(param_id)

                    with ui.column().classes("w-full min-w-0 max-w-full gap-1"):
                        ui.label(param_schema.label).classes(
                            "font-semibold text-sm text-zinc-800"
                        )
                        if param_value is None:
                            ui.label("(not provided)").classes(
                                "text-sm text-zinc-400 italic"
                            )
                        else:
                            _readonly_value_block(str(param_value))

    logger.debug("Read-only form (component) rendered")
