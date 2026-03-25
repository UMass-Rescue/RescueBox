import logging
from nicegui import ui
from rb.api.models import TaskSchema, RequestBody, ResponseBody
from frontend.components.results import ResultsPreview
from frontend.components.results.image_summary_results_view import (
    augment_response_model_dump_for_image_summary,
)
from frontend.components.shared import create_breadcrumbs
from frontend.pages.jobs.job_utils import extract_job_fields
from frontend.pages.jobs.components import render_error_status, render_job_action_buttons, render_compact_inputs_summary

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def render_job_outputs_card(container, api_client, job):
    """
    Render job outputs inside provided container. This is the extracted component
    previously inline inside `job_details.render_job_outputs`.
    """
    job_fields = extract_job_fields(job)
    job_uid = job_fields['uid']
    response = job_fields['response']
    status = job_fields['status']
    status_text = job_fields['statusText']
    task_schema_dict = job_fields['taskSchema']
    endpoint = job_fields['endpoint']

    logger.info("Rendering job outputs for job: %s", job_uid)

    if not response:
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
        ui.label(f'Invalid response format: {str(e)}').classes('text-red-600')
        return

    with ui.card().classes('w-full min-w-0 max-w-full self-stretch bg-white border border-gray-300 p-6'):
        create_breadcrumbs([
            {'label': 'Jobs', 'link': '/jobs'},
            {'label': f'Job {job_uid[:8]}...', 'link': f'/jobs/{job_uid}'},
            {'label': 'Results'}
        ])

        # Header and action buttons
        with ui.row().classes('items-center justify-between mb-4'):
            try:
                task_schema = TaskSchema(**task_schema_dict) if isinstance(task_schema_dict, dict) else task_schema_dict
                task_title = 'Results for ' + endpoint
            except Exception:
                task_title = task_schema_dict.get('shortTitle', 'Results') if isinstance(task_schema_dict, dict) else 'Results'

            ui.label(task_title).classes('text-2xl font-bold')
            with ui.row().classes('gap-2 items-center') as actions_row:
                try:
                    from frontend.components.jobs.job_actions_component import render_job_actions
                    render_job_actions(actions_row, job_fields)
                except Exception:
                    # Fallback to original behavior
                    render_job_action_buttons(job_fields)
                # audit trail button may be async; caller handles if needed
                # kept out of component for now

        # Inputs/parameters summary
        try:
            request_body_dict = job_fields.get('request', {})
            if request_body_dict and task_schema_dict:
                task_schema = TaskSchema(**task_schema_dict) if isinstance(task_schema_dict, dict) else task_schema_dict
                request_body = RequestBody(**request_body_dict) if isinstance(request_body_dict, dict) else request_body_dict
                render_compact_inputs_summary(task_schema, request_body)
        except Exception as e:
            logger.debug("Could not render inputs summary: %s", str(e))

        # Results preview
        logger.debug("Rendering results preview in outputs card")
        results_container = ui.column().classes('w-full gap-4')
        preview_dump = augment_response_model_dump_for_image_summary(
            response_body.model_dump(), job_fields
        )
        ResultsPreview.render(results_container, preview_dump)
        logger.info("Job outputs rendered successfully (component)")

