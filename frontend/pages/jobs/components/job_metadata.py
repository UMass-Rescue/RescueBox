"""
Job Metadata Components

This module provides UI components for rendering job metadata, model information,
and status displays.
"""

import logging
from datetime import datetime
from nicegui import ui
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add backend models to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'src'))

from rb.api.models import TaskSchema, RequestBody

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def extract_job_fields(job):
    """
    Extract job fields from JobRecord or dict.

    Provides backward compatibility for both Pydantic models and dictionaries.

    Args:
        job: JobRecord Pydantic model or dict

    Returns:
        Dict[str, Any]: Dictionary with job fields
    """
    if hasattr(job, 'model_dump'):
        # Pydantic model
        return job.model_dump()
    else:
        # Dict - return as is
        return job


async def render_model_info(api_client, job_fields: Dict[str, Any]):
    """
    Render model information section.

    Displays model name and provides a link to model details page, or shows
    endpoint info for chatbot jobs.

    Args:
        api_client: API client instance for fetching model info
        job_fields: Job fields dictionary
    """
    model_uid = job_fields.get('modelUid')

    if model_uid:
        try:
            from frontend.pages.jobs.job_utils import get_plugin_name
            plugin_name = await get_plugin_name(api_client, model_uid)
            if plugin_name:
                with ui.row().classes('items-center gap-2 mt-4'):
                    ui.label('Model:').classes('font-semibold')
                    ui.label(plugin_name).classes('flex-1')
                    ui.button(
                        'Inspect',
                        on_click=lambda: ui.navigate.to(f'/models/{model_uid}/details')
                    ).classes('bg-blue-600 text-white')
            else:
                # Try fetching from API
                response = await api_client.get(f'/models/{model_uid}')
                if response.status_code == 200:
                    model = response.json()
                    with ui.row().classes('items-center gap-2 mt-4'):
                        ui.label('Model:').classes('font-semibold')
                        ui.label(model.get('name', 'Unknown')).classes('flex-1')
                        ui.button(
                            'Inspect',
                            on_click=lambda: ui.navigate.to(f'/models/{model_uid}/details')
                        ).classes('bg-blue-600 text-white')
        except Exception as e:
            logger.debug("Could not fetch model info: %s", str(e))
            pass
    else:
        # For jobs without modelUid (e.g., chatbot jobs), show endpoint info
        endpoint = job_fields.get('endpoint') or job_fields.get('taskUid')
        if endpoint:
            with ui.row().classes('items-center gap-2 mt-4'):
                ui.label('Model:').classes('font-semibold')
                ui.label(endpoint).classes('flex-1 text-sm text-gray-600')
                logger.debug("Job uses endpoint directly: %s", endpoint)


def render_error_status(status: str, status_text: Optional[str] = None):
    """
    Render error status card for failed jobs.

    Displays a visually distinct error card when a job has failed or has no response.

    Args:
        status (str): Job status (e.g., 'Failed', 'Error')
        status_text (Optional[str]): Additional status text/error message
    """
    with ui.card().classes('bg-red-50 border border-red-300 p-6'):
        ui.label('Job Failed').classes('text-2xl font-bold text-red-700 mb-2')
        ui.label(f'Status: {status}').classes('text-lg text-red-600')
        if status_text:
            ui.label(status_text).classes('text-sm text-red-500 mt-2')


def render_job_metadata(job_fields: Dict[str, Any]):
    """
    Render basic job metadata information.

    Displays job UID, timestamps, and status in a structured format.

    Args:
        job_fields (Dict[str, Any]): Job fields dictionary
    """
    job_uid = job_fields.get('uid', 'Unknown')
    start_time = job_fields.get('startTime')
    end_time = job_fields.get('endTime')
    status = job_fields.get('status', 'Unknown')

    with ui.column().classes('gap-2 mt-4'):
        ui.label('Job ID:').classes('font-semibold')
        ui.label(job_uid).classes('text-sm text-gray-600 mb-2')

        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time) if isinstance(start_time, str) else start_time
                ui.label(f'Started: {start_dt.strftime("%Y-%m-%d %H:%M:%S")}').classes('text-sm')
            except (ValueError, AttributeError):
                ui.label(f'Started: {start_time}').classes('text-sm')

        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time) if isinstance(end_time, str) else end_time
                ui.label(f'Ended: {end_dt.strftime("%Y-%m-%d %H:%M:%S")}').classes('text-sm')
            except (ValueError, AttributeError):
                ui.label(f'Ended: {end_time}').classes('text-sm')

        status_color = {
            'Completed': 'text-green-600',
            'Running': 'text-blue-600',
            'Failed': 'text-red-600',
            'Canceled': 'text-gray-600'
        }.get(status, 'text-gray-600')

        ui.label(f'Status: {status}').classes(f'text-sm font-semibold {status_color}')
