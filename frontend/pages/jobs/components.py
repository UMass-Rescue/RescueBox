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

    return ui.button("📋 Export Audit Trail", on_click=export_audit).classes(
        "rb-brand-primary text-white rounded-xl"
    )


def render_job_action_buttons(job_fields: Dict[str, Any]):
    model_uid = job_fields.get("modelUid")
    with ui.row().classes("gap-2"):
        if model_uid:
            ui.button(
                "Model Doc",
                on_click=lambda: ui.navigate.to(f"/models/{model_uid}/details"),
            ).classes("rb-brand-primary text-white")
            ui.button(
                "Run Model", on_click=lambda: ui.navigate.to(f"/models/{model_uid}/run")
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
    with ui.card().classes("bg-red-50 border border-red-300 p-6"):
        ui.label("Job Failed").classes("text-2xl font-bold text-red-800 mb-2")
        ui.label(f"Status: {status}").classes("text-lg text-red-600")
        if status_text:
            ui.label(status_text).classes("text-sm text-red-500 mt-2")


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
