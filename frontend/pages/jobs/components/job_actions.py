"""
Job Action Components

This module provides UI components for rendering job action buttons and navigation.
"""

import logging
from nicegui import ui
from typing import Dict, Any

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_job_action_buttons(job_fields: Dict[str, Any]):
    """
    Render action buttons for job.

    Displays action buttons (Model Doc, Run Model, Re-submit) based on
    job type (traditional model/task vs chatbot endpoint).

    Args:
        job_fields (Dict[str, Any]): Extracted job fields from extract_job_fields()

    Returns:
        None: UI is added directly to the current context

    Tips:
    - Model Doc and Run Model buttons only shown for traditional jobs (with modelUid)
    - Re-submit button shown for both chatbot jobs (endpoint) and traditional jobs (taskUid)
    - Buttons are color-coded for different actions
    """
    model_uid = job_fields.get('modelUid')
    endpoint = job_fields.get('endpoint')
    task_uid = job_fields.get('taskUid')
    job_uid = job_fields.get('uid')

    with ui.row().classes('gap-2'):
        # Note: Jobs created via chatbot use endpoints directly (e.g., "audio/transcribe")
        # and may not have modelUid/taskUid. Only show model buttons if available.
        if model_uid:
            ui.button(
                'Model Doc',
                on_click=lambda: ui.navigate.to(f'/models/{model_uid}/details')
            ).classes('bg-blue-600 text-white')

            ui.button(
                'Run Model',
                on_click=lambda: ui.navigate.to(f'/models/{model_uid}/run')
            ).classes('bg-green-600 text-white')

