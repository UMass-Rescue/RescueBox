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
    Render the job details panel: metadata, model info, and read-only form.
    """
    job_uid = job_fields.get('uid')
    request_body_dict = job_fields.get('request', {})
    task_schema_dict = job_fields.get('taskSchema')

    with container:
        with ui.card().classes('bg-white border border-gray-300 p-6'):
            # Job metadata header
            with ui.column().classes('gap-4'):
                ui.label('Job Information').classes('text-2xl font-bold')

                # Basic info
                render_job_metadata(job_fields)

                # Model info (async)
                try:
                    await render_model_info(api_client, job_fields)
                except Exception as e:
                    logger.debug("Failed to render model info: %s", e)

                # Request body (read-only form)
                if task_schema_dict:
                    try:
                        task_schema = TaskSchema(**task_schema_dict) if isinstance(task_schema_dict, dict) else task_schema_dict
                        request_body = RequestBody(**request_body_dict) if isinstance(request_body_dict, dict) else request_body_dict
                        render_readonly_form(task_schema, request_body)
                    except Exception as e:
                        logger.error("Error parsing schema in details panel: %s", str(e))
                        ui.label(f'Error parsing schema: {str(e)}').classes('text-red-600')

