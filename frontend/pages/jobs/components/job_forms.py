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
        # Fallback to inline rendering (original behavior)
        with ui.expansion('View inputs & parameters', icon='description').classes('w-full mb-4'):
            with ui.column().classes('gap-3 p-4 bg-zinc-50 rounded'):
                # Inputs
                if task_schema.inputs:
                    ui.label('Inputs').classes('font-semibold text-lg')
                    for input_schema in task_schema.inputs:
                        field_id = input_schema.key
                        field_input = request_body.inputs.get(field_id)

                        with ui.row().classes('items-start gap-2'):
                            ui.label(input_schema.label).classes('w-32 font-semibold text-sm')

                            if field_input:
                                # Extract value from Input union type
                                input_root = field_input.root if hasattr(field_input, 'root') else field_input

                                if hasattr(input_root, 'path'):
                                    # FileInput or DirectoryInput
                                    path_str = str(input_root.path)
                                    # Truncate long paths
                                    display_path = path_str if len(path_str) < 80 else path_str[:77] + '...'
                                    ui.label(display_path).classes('flex-1 text-sm font-mono text-zinc-700')
                                elif hasattr(input_root, 'text'):
                                    # TextInput - show first line
                                    text = input_root.text
                                    first_line = text.split('\\n')[0] if '\\n' in text else text
                                    display_text = first_line if len(first_line) < 100 else first_line[:97] + '...'
                                    ui.label(display_text).classes('flex-1 text-sm text-zinc-700')
                                else:
                                    # Batch types or other
                                    ui.label(str(input_root)).classes('flex-1 text-sm text-zinc-700')
                            else:
                                ui.label('(not provided)').classes('flex-1 text-sm text-zinc-400 italic')

                # Parameters
                if task_schema.parameters:
                    ui.label('Parameters').classes('font-semibold text-lg mt-2')
                    for param_schema in task_schema.parameters:
                        param_id = param_schema.key
                        param_value = request_body.parameters.get(param_id)

                        with ui.row().classes('items-center gap-2'):
                            ui.label(param_schema.label).classes('w-32 font-semibold text-sm')
                            ui.label(str(param_value) if param_value is not None else '(not provided)').classes('flex-1 text-sm text-zinc-700')


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
        ui.label('Request Inputs and Parameters').classes('text-xl font-bold mt-6')

        # Render form fields as read-only (full width, wrap long paths — matches component)
        with ui.column().classes('gap-4 mt-4 w-full min-w-0 max-w-full'):
            # Inputs
            if task_schema.inputs:
                ui.label('Inputs').classes('font-semibold text-lg')
                for input_schema in task_schema.inputs:
                    field_id = input_schema.key
                    field_input = request_body.inputs.get(field_id)

                    with ui.column().classes('w-full min-w-0 max-w-full gap-1'):
                        ui.label(input_schema.label).classes('font-semibold text-sm text-zinc-800')

                        if field_input:
                            input_root = field_input.root if hasattr(field_input, 'root') else field_input

                            if hasattr(input_root, 'path'):
                                ui.textarea(
                                    label='',
                                    value=str(input_root.path),
                                ).classes('w-full min-w-0 max-w-full font-mono text-xs break-all').props(
                                    'readonly outlined dense autogrow'
                                )
                            elif hasattr(input_root, 'text'):
                                ui.textarea(
                                    label='',
                                    value=input_root.text
                                ).classes('w-full min-w-0 max-w-full text-sm break-words whitespace-pre-wrap').props(
                                    'readonly outlined dense autogrow'
                                )
                            else:
                                ui.textarea(
                                    label='',
                                    value=str(input_root),
                                ).classes('w-full min-w-0 max-w-full font-mono text-xs break-all').props(
                                    'readonly outlined dense autogrow'
                                )
                        else:
                            ui.label('(not provided)').classes('text-sm text-zinc-400 italic')

            # Parameters
            if task_schema.parameters:
                ui.label('Parameters').classes('font-semibold text-lg mt-4')
                for param_schema in task_schema.parameters:
                    param_id = param_schema.key
                    param_value = request_body.parameters.get(param_id)

                    with ui.column().classes('w-full min-w-0 max-w-full gap-1'):
                        ui.label(param_schema.label).classes('font-semibold text-sm text-zinc-800')
                        if param_value is None:
                            ui.label('(not provided)').classes('text-sm text-zinc-400 italic')
                        else:
                            ui.textarea(
                                label='',
                                value=str(param_value),
                            ).classes('w-full min-w-0 max-w-full text-sm break-all').props(
                                'readonly outlined dense autogrow'
                            )
