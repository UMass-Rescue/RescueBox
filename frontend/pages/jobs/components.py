import logging
from datetime import datetime
from nicegui import ui
from typing import Dict, Any, Optional
from frontend.utils import (
    generate_audit_trail_for_job,
    notify_info,
    notify_success,
    notify_error,
)

logger = logging.getLogger(__name__)


async def create_audit_trail_button(job_id: str):
    async def export_audit():
        try:
            notify_info("Generating audit trail...")
            audit_trail = await generate_audit_trail_for_job(job_id)
            if "error" in audit_trail:
                notify_error(f"Error: {audit_trail['error']}")
                return

            # Simple markdown export for now as per original code's pattern
            from frontend.utils import format_audit_trail_markdown

            markdown_content = format_audit_trail_markdown(audit_trail)
            filename = f"audit_trail_job_{job_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            ui.download(markdown_content.encode("utf-8"), filename=filename)
            notify_success(f"Audit trail exported: {filename}")
        except Exception as e:
            logger.error("Error exporting audit trail: %s", e)
            notify_error(f"Error exporting audit trail: {str(e)}")

    return ui.button(
        "Export Audit Trail",
        icon="assignment_turned_in",
        color=None,
        on_click=export_audit,
    ).classes(
        "bg-slate-100 hover:bg-slate-200 text-slate-800 px-4 py-2 rounded-lg font-medium transition-colors border border-slate-200"
    )


def render_job_action_buttons(job_fields: Dict[str, Any]):
    model_uid = job_fields.get("modelUid")
    with ui.row().classes("gap-2"):
        if model_uid:
            ui.button(
                "Model Doc",
                color=None,
                on_click=lambda: ui.navigate.to(f"/models/{model_uid}/details"),
            ).classes("rb-brand-primary text-white")
            ui.button(
                "Run Model",
                color=None,
                on_click=lambda: ui.navigate.to(f"/models/{model_uid}/run"),
            ).classes("rb-brand-primary text-white rounded-xl")


def render_compact_inputs_summary(task_schema, request_body):
    try:
        from frontend.components.jobs import (
            render_compact_inputs_summary as _render_compact,
        )

        _render_compact(ui.column(), task_schema, request_body)
    except Exception as e:
        logger.error("Failed to render compact inputs: %s", e)


def render_readonly_form(task_schema, request_body):
    try:
        from frontend.components.jobs import render_readonly_form as _render_readonly

        _render_readonly(
            ui.column().classes("w-full min-w-0"), task_schema, request_body
        )
    except Exception as e:
        logger.error("Failed to render readonly form: %s", e)


def render_error_status(status: str, status_text: Optional[str] = None):
    with ui.card().classes(
        "bg-rose-50 border border-rose-200 p-6 rounded-2xl shadow-sm border-t-4 border-t-rose-500"
    ):
        with ui.row().classes("items-center gap-2 mb-2"):
            ui.icon("error", size="md").classes("text-rose-600")
            ui.label("Job Failed").classes("text-2xl font-bold text-rose-800")
        ui.label(f"Status: {status}").classes("text-lg text-rose-700 font-medium")
        if status_text:
            ui.label(status_text).classes(
                "text-sm text-rose-600 mt-2 bg-white/50 p-3 rounded-lg border border-rose-100 whitespace-pre-wrap"
            )


async def render_model_info(api_client, job_fields: Dict[str, Any]):
    model_uid = job_fields.get("modelUid")
    if not model_uid:
        return

    try:
        from frontend.pages.jobs.utils import get_plugin_name

        name = await get_plugin_name(api_client, model_uid) or model_uid
        with ui.column().classes("gap-1 mt-4"):
            ui.label("Plugin / Model").classes("font-semibold")
            with ui.row().classes("items-center gap-2"):
                ui.icon("smart_toy", size="sm").classes("text-zinc-500")
                ui.label(name).classes("text-sm text-zinc-800")
                ui.label(f"({model_uid})").classes("text-xs text-zinc-500 font-mono")
    except Exception as e:
        logger.debug("Failed to render model info: %s", e)


def render_job_metadata(job_fields: Dict[str, Any]):
    with ui.column().classes("gap-2 mt-4"):
        ui.label("Job ID:").classes("font-semibold")
        ui.label(job_fields.get("uid", "Unknown")).classes("text-sm text-zinc-600 mb-2")


async def render_job_outputs_card(container, api_client, job):
    from frontend.components.jobs import render_job_outputs_card as _render

    await _render(container, api_client, job)


async def render_job_details_panel(container, api_client, job_fields):
    from frontend.components.jobs import render_job_details_panel as _render

    await _render(container, api_client, job_fields)
