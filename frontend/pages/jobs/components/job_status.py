"""
Job Status Components

This module provides UI components for rendering job status information and error displays.
"""

import logging
from nicegui import ui
from typing import Optional

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_error_status(status: str, status_text: Optional[str] = None):
    """
    Render error status card for failed jobs.

    Displays a visually distinct error card when a job has failed or has no response.

    Args:
        status (str): Job status (e.g., 'Failed', 'Error')
        status_text (Optional[str]): Additional status text/error message
    """
    with ui.card().classes('bg-red-50 border border-red-300 p-6'):
        ui.label('Job Failed').classes('text-2xl font-bold text-black-700 mb-2')
        ui.label(f'Status: {status}').classes('text-lg text-black-600')
        if status_text:
            ui.label(status_text).classes('text-sm text-black-500 mt-2')
