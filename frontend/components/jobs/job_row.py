"""
Job Row Component

This module provides the render_job_row function for displaying job information
in a table row format. The row shows job status, timestamps, and action buttons.
"""

import logging
from nicegui import ui
from typing import Dict, Optional, Callable
from datetime import datetime

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_job_row(
    container, 
    job: Dict, 
    plugin_name: Optional[str] = None, 
    on_view: Optional[Callable] = None, 
    on_cancel: Optional[Callable] = None, 
    on_delete: Optional[Callable] = None
):
    """
    Render a job row in table format.
    
    This function creates a table row component displaying job information including
    model name, status, timestamps, and action buttons. The row uses color-coding
    to indicate job status (Running, Completed, Failed, Canceled).
    
    Design Features:
    - Status color coding: Different colors for different job statuses
    - Formatted timestamps: Human-readable date/time format
    - Hover effects: Background color change on hover
    - Conditional buttons: Action buttons shown based on job status
    
    Args:
        container: NiceGUI container element to add the row to (typically ui.row() or table body)
        job (Dict): Job data dictionary containing:
            - 'uid' (str): Unique job identifier
            - 'status' (str): Job status ('Running', 'Completed', 'Failed', 'Canceled')
            - 'startTime' (str, optional): ISO format start timestamp
            - 'endTime' (str, optional): ISO format end timestamp
            - Additional job metadata
        plugin_name (Optional[str]): Display name of the model. If not provided,
            'Unknown' will be displayed. Defaults to None
        on_view (Optional[Callable]): Callback function called when View button is clicked.
            Receives job UID: on_view(job['uid'])
        on_cancel (Optional[Callable]): Callback function called when Cancel button is clicked.
            Only shown for running jobs. Receives job UID: on_cancel(job['uid'])
        on_delete (Optional[Callable]): Callback function called when Delete button is clicked.
            Receives job UID: on_delete(job['uid'])
    
    Returns:
        None: This function modifies the container directly
    
    Examples:
        >>> render_job_row(
        ...     container=table_body,
        ...     job={'uid': 'job-123', 'status': 'Running', 'startTime': '2024-01-01T10:00:00Z'},
        ...     plugin_name='Face Detection',
        ...     on_view=lambda uid: ui.navigate.to(f'/jobs/{uid}'),
        ...     on_cancel=lambda uid: cancel_job(uid)
        ... )
    
    Tips:
    - Timestamps are automatically formatted from ISO format
    - Status colors are predefined but can be customized
    - Buttons are conditionally rendered based on callbacks and job status
    - Row uses hover effects for better user experience
    """
    logger.info("Rendering job row for job: %s (Status: %s)", job.get('uid', 'Unknown'), job.get('status', 'Unknown'))
    
    status = job.get('status', 'Unknown')
    status_colors = {
        'Running': 'text-blue-600',
        'Completed': 'text-green-600',
        'Failed': 'text-red-600',
        'Canceled': 'text-gray-600'
    }
    status_color = status_colors.get(status, 'text-gray-600')
    logger.debug("Job status: %s, color class: %s", status, status_color)
    
    # Format timestamps
    start_time_str = 'N/A'
    if job.get('startTime'):
        try:
            start_time = datetime.fromisoformat(job['startTime'].replace('Z', '+00:00'))
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M')
            logger.debug("Formatted start time: %s", start_time_str)
        except Exception as e:
            logger.warning("Failed to parse start time: %s, error: %s", job['startTime'], e)
            start_time_str = job['startTime']
    
    end_time_str = 'N/A'
    if job.get('endTime'):
        try:
            end_time = datetime.fromisoformat(job['endTime'].replace('Z', '+00:00'))
            end_time_str = end_time.strftime('%Y-%m-%d %H:%M')
            logger.debug("Formatted end time: %s", end_time_str)
        except Exception as e:
            logger.warning("Failed to parse end time: %s, error: %s", job['endTime'], e)
            end_time_str = job['endTime']
    
    job_uid = job.get('uid', 'N/A')
    with container:
        with ui.row().classes('p-4 border-b hover:bg-gray-50 items-center w-full flex-nowrap gap-2'):
            # Job ID - truncated with ellipsis, full ID on hover
            with ui.element('div').classes('w-40 min-w-0 shrink-0'):
                id_label = ui.label(job_uid).classes('font-mono text-sm truncate block')
                id_label.tooltip(job_uid)

            # Model name (and notes indicator)
            with ui.element('div').classes('flex-1 min-w-0 overflow-hidden flex items-center gap-2'):
                ui.label(plugin_name or 'Unknown').classes('truncate block')
                if job.get('caseNotes'):
                    notes_preview = (job['caseNotes'] or '')[:50]
                    if len(job.get('caseNotes', '') or '') > 50:
                        notes_preview += '…'
                    ui.icon('description', size='sm').classes('text-gray-500 shrink-0').tooltip(notes_preview)
            
            # Times (start / end)
            with ui.column().classes('w-64 shrink-0'):
                ui.label(start_time_str).classes('text-sm')
                ui.label(end_time_str).classes('text-xs text-gray-600')
            
            # Status
            ui.label(status).classes(f'w-32 shrink-0 {status_color} font-semibold')
            
            # Actions
            with ui.row().classes('gap-2 w-48 shrink-0'):
                if on_view:
                    ui.button(
                        'View',
                        on_click=lambda j=job: on_view(j['uid']) if on_view else None
                    ).classes('bg-blue-600 text-white text-sm')
                
                if status == 'Running' and on_cancel:
                    ui.button(
                        'Cancel',
                        on_click=lambda j=job: on_cancel(j['uid']) if on_cancel else None
                    ).classes('bg-red-600 text-white text-sm')
                elif status != 'Running' and on_delete:
                    ui.button(
                        'Delete',
                        on_click=lambda j=job: on_delete(j['uid']) if on_delete else None
                    ).classes('bg-gray-600 text-white text-sm')
                    logger.debug("Delete button added")
    
    logger.info("Job row rendered successfully")