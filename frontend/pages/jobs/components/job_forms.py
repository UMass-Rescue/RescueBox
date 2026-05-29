"""
Job Form Components

This module provides UI components for rendering job input forms and parameters.
"""

import logging
from nicegui import ui
from pathlib import Path
import sys

# Add backend models to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'src'))

from rb.api.models import TaskSchema, RequestBody

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_compact_inputs_summary(task_schema: TaskSchema, request_body: RequestBody):
    """
    Render a compact summary of inputs and parameters.

    Displays inputs and parameters in a collapsible, compact format suitable
    for displaying above results.

    Args:
        task_schema (TaskSchema): Task schema defining inputs and parameters
        request_body (RequestBody): Request body containing actual values

    Returns:
        None: UI is added directly to the current context

    Tips:
    - Shows inputs and parameters in a collapsible expansion panel
    - Uses compact display format
    - File paths are truncated if too long
    - Text inputs show first line only in summary
    """
    logger.debug("Rendering compact inputs summary")
    try:
        from frontend.components.jobs.compact_inputs_summary import render_compact_inputs_summary as _render_compact
        _render_compact(ui.column(), task_schema, request_body)
        logger.debug("Compact inputs summary rendered via component")
    except Exception as e:
        logger.exception("Component render failed, falling back to inline: %s", e)
        


def render_readonly_form(task_schema: TaskSchema, request_body: RequestBody):
    """
    Render read-only form for job inputs and parameters.

    Displays job inputs and parameters as read-only form fields based on
    the task schema and request body.

    Args:
        task_schema (TaskSchema): Task schema defining inputs and parameters
        request_body (RequestBody): Request body containing actual values

    Returns:
        None: UI is added directly to the current context

    Tips:
    - Inputs are rendered with appropriate UI components (input, textarea) based on type
    - Parameters are rendered as simple text inputs
    - All fields are read-only (readonly prop)
    - FileInput/DirectoryInput show path, TextInput shows text content
    """
    logger.debug("Rendering read-only form")
    try:
        from frontend.components.jobs.readonly_form import render_readonly_form as _render_readonly
        _render_readonly(
            ui.column().classes("w-full min-w-0 max-w-full"), task_schema, request_body
        )
        logger.debug("Read-only form rendered via component")
    except Exception as e:
        logger.exception("Component render failed, falling back to inline: %s", e)
