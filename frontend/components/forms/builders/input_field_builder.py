"""
Input Field Builder

This module provides functions for creating input form fields.
"""

import logging
from nicegui import ui
from typing import Dict
from pathlib import Path
import sys

# Add backend models to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

from rb.api.models import (
    InputSchema,
    InputType,
    DirectoryInput,
    FileInput,
)
from frontend.utils.file_browser import browse_directory_simple, browse_file_simple

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def create_input_field(
    input_schema: InputSchema,
    form_widgets: Dict,
    initial_values: Dict
) -> None:
    """
    Create an input field from InputSchema.

    This function creates appropriate UI controls based on the input type:
    - DIRECTORY: Input field with browse button
    - FILE: Input field with browse button
    - TEXT: Text input field
    - TEXTAREA: Multi-line textarea field

    The widget is stored in form_widgets for later value retrieval.

    Args:
        input_schema (InputSchema): Schema defining the input field
        form_widgets (Dict): Dictionary to store widget references (keyed by field_id)
        initial_values (Dict): Dictionary containing initial form values

    Returns:
        None: Field is added directly to the current UI context

    Tips:
    - Initial values are read from initial_values dict
    - Widgets are stored by field_id for form data collection
    - Browse buttons trigger file/directory browser dialogs
    """
    field_id = input_schema.key
    label = input_schema.label
    input_type = input_schema.input_type
    subtitle = input_schema.subtitle or ''

    logger.debug("Creating input field: %s (type: %s)", field_id, input_type)

    initial_value = initial_values.get(field_id, {})

    with ui.column().classes('gap-2 w-full min-w-0'):
        label_text = label
        if subtitle:
            ui.label(label_text).classes('font-semibold')
            ui.label(subtitle).classes('text-sm text-gray-500')
        else:
            ui.label(label_text).classes('font-semibold')

        # Handle InputType enum
        if isinstance(input_type, InputType):
            if input_type == InputType.DIRECTORY:
                with ui.column().classes('w-full min-w-0'):
                    try:
                        from frontend.components.forms.fields.input_widgets import create_directory_input
                        create_directory_input(field_id, initial_value, form_widgets)
                    except Exception:
                        # Fallback to inline behavior if component load fails
                        # Make the directory input occupy full width and move the Browse button to its own row
                        # Place the label above the input (avoid floating label that constrains layout)
                        ui.label('Directory path').classes('font-semibold')
                        with ui.column().classes('w-full'):
                            dir_input = ui.input(
                                placeholder='/path/to/directory',
                                value=initial_value.get('path', '') if isinstance(initial_value, dict) else ''
                            ).classes('w-full')

                            # Visible full-path label under the input to avoid horizontal scrolling
                            full_path_label = ui.label(dir_input.value or '').classes('text-xs font-mono text-gray-600 mt-1 break-words')

                        # Add validation feedback (hidden until user enters a value)
                        validation_status = ui.icon('').classes('text-gray-400 q-mr-sm')
                        validation_status.hide()

                        def validate_directory_path():
                            path = dir_input.value.strip()
                            # update visible full path label
                            try:
                                full_path_label.text = path
                            except Exception:
                                pass
                            if not path:
                                validation_status.name = ''
                                validation_status.hide()
                                return

                            p = Path(path)
                            if p.exists() and p.is_dir():
                                validation_status.name = 'check_circle'
                                validation_status.classes('text-green-500 q-mr-sm', remove='text-red-500 text-gray-400')
                                validation_status.show()
                            else:
                                validation_status.name = 'error'
                                validation_status.classes('text-red-500 q-mr-sm', remove='text-green-500 text-gray-400')
                                validation_status.show()

                        dir_input.on('change', validate_directory_path)
                        if dir_input.value:
                            validate_directory_path()

                        # Browse button on the next line for clarity
                        with ui.row().classes('gap-2'):
                            ui.space()
                            with ui.row().classes('items-center gap-2'):
                                validation_status
                                ui.button(
                                    'Browse',
                                    on_click=lambda: browse_directory_simple(
                                        dir_input, on_after_select=validate_directory_path
                                    ),
                                ).classes('bg-gray-300')
                        form_widgets[field_id] = dir_input

            elif input_type == InputType.FILE:
                with ui.column().classes('w-full min-w-0 gap-2'):
                    try:
                        from frontend.components.forms.fields.input_widgets import create_file_input
                        create_file_input(field_id, initial_value, form_widgets)
                    except Exception:
                        with ui.column().classes('w-full min-w-0 gap-1'):
                            ui.label('File path').classes('text-sm font-medium text-gray-700')
                            with ui.row().classes('w-full min-w-0 items-center gap-2 flex-nowrap'):
                                file_input = ui.input(
                                    label='',
                                    placeholder='/path/to/file',
                                    value=initial_value.get('path', '') if isinstance(initial_value, dict) else ''
                                ).classes('flex-1 min-w-0').props('outlined dense')

                                file_validation_status = ui.icon('').classes('text-gray-400 shrink-0')
                                file_validation_status.hide()

                                def validate_file_path():
                                    path = file_input.value.strip()
                                    if not path:
                                        file_validation_status.name = ''
                                        file_validation_status.hide()
                                        return

                                    p = Path(path)
                                    if p.exists() and p.is_file():
                                        file_validation_status.name = 'check_circle'
                                        file_validation_status.classes('text-green-500', remove='text-red-500 text-gray-400')
                                        file_validation_status.show()
                                    else:
                                        file_validation_status.name = 'error'
                                        file_validation_status.classes('text-red-500', remove='text-green-500 text-gray-400')
                                        file_validation_status.show()

                                file_input.on('change', validate_file_path)
                                if file_input.value:
                                    validate_file_path()

                                ui.button(
                                    'Browse',
                                    on_click=lambda: browse_file_simple(
                                        file_input, on_after_select=validate_file_path
                                    ),
                                ).classes('shrink-0 bg-gray-300')
                        form_widgets[field_id] = file_input

            elif input_type == InputType.TEXTAREA:
                text_input = ui.textarea(
                    label='',
                    placeholder='Enter text...',
                    value=initial_value.get('text', '') if isinstance(initial_value, dict) else ''
                ).classes('w-full')
                form_widgets[field_id] = text_input

            elif input_type == InputType.TEXT:
                text_input = ui.input(
                    label='',
                    placeholder='Enter text...',
                    value=initial_value.get('text', '') if isinstance(initial_value, dict) else ''
                ).classes('w-full')
                form_widgets[field_id] = text_input

    logger.debug("Input field created: %s", field_id)
