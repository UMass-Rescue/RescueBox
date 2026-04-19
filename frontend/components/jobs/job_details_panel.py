import logging
from nicegui import ui
from typing import Any
from rb.api.models import TaskSchema, RequestBody
from frontend.pages.jobs.components import (
    render_job_metadata,
    render_model_info,
    render_readonly_form,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def render_job_details_panel(container: ui.element, api_client, job_fields: dict) -> None:
    """
    Render the job details panel: metadata, model info, case notes, and read-only form.
    """
    job_uid = job_fields.get('uid')
    request_body_dict = job_fields.get('request', {})
    task_schema_dict = job_fields.get('taskSchema')
    case_notes = job_fields.get('caseNotes')
    pipeline_filter = job_fields.get('pipelineMetadataFilterCriteria')

    with container:
        with ui.card().classes('w-full min-w-0 max-w-full self-stretch bg-white border border-zinc-300 p-6'):
            # Job metadata header
            with ui.column().classes('gap-4 w-full min-w-0 max-w-full'):
                ui.label('Job Information').classes('text-2xl font-bold')

                # Classifier metadata filter (age/gender pipeline → next step), if recorded
                if pipeline_filter is not None:
                    with ui.column().classes('gap-2'):
                        ui.label('Classifier filter (next pipeline step)').classes(
                            'font-semibold text-zinc-700'
                        )
                        _txt = (pipeline_filter or '').strip()
                        ui.label(
                            _txt
                            if _txt
                            else 'No age/gender filter — all images were eligible for the next step.'
                        ).classes(
                            'text-sm text-zinc-800 whitespace-pre-wrap rounded p-3 '
                            'bg-amber-50/80 border border-amber-100'
                        )

                # Case notes section
                if case_notes:
                    with ui.column().classes('gap-2'):
                        ui.label('Case Notes').classes('font-semibold text-zinc-700')
                        ui.label(case_notes).classes('text-zinc-800 whitespace-pre-wrap rounded p-3 bg-zinc-50 border border-zinc-200')
                elif case_notes is not None and case_notes == '':
                    pass  # Empty notes, don't show section
                # If caseNotes key not present (older jobs), don't show

                # Basic info
                render_job_metadata(job_fields)

                # Model info (async)
                try:
                    await render_model_info(api_client, job_fields)
                except Exception as e:
                    logger.debug("Failed to render model info: %s", e)

                # Failed runs: keep the message with other job fields (not only under Outputs).
                _status = str(job_fields.get("status") or "")
                _status_text = (job_fields.get("statusText") or "").strip()
                if _status == "Failed":
                    with ui.column().classes("gap-2 w-full min-w-0"):
                        ui.label("Failure message").classes("font-semibold text-zinc-800")
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
                        task_schema = TaskSchema(**task_schema_dict) if isinstance(task_schema_dict, dict) else task_schema_dict
                        request_body = RequestBody(**request_body_dict) if isinstance(request_body_dict, dict) else request_body_dict
                        render_readonly_form(task_schema, request_body)
                    except Exception as e:
                        logger.error("Error parsing schema in details panel: %s", str(e))
                        ui.label(f'Error parsing schema: {str(e)}').classes('text-red-600')

