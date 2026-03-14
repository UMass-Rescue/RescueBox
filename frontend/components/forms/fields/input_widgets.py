import logging
from nicegui import ui
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_directory_input(field_id: str, initial_value: Dict[str, Any], form_widgets: Dict) -> Any:
    """
    Create a directory input row with validation and a Browse button.
    Intended to be called inside a `with ui.row().classes('items-center gap-2'):` context.
    """
    from rb.api.models import DirectoryInput
    from frontend.utils.file_browser import browse_directory_simple

    dir_input = ui.input(
        label='Directory path',
        placeholder='/path/to/directory',
        value=initial_value.get('path', '') if isinstance(initial_value, dict) else ''
    ).classes('flex-1')

    # Add validation feedback
    validation_status = ui.icon('').classes('text-gray-400 q-mr-sm')

    def validate_directory_path():
        path = dir_input.value.strip()
        if not path:
            validation_status.name = ''
            return

        try:
            DirectoryInput(path=Path(path))
            validation_status.name = 'check_circle'
            validation_status.classes('text-green-500 q-mr-sm', remove='text-red-500 text-gray-400')
        except Exception:
            validation_status.name = 'error'
            validation_status.classes('text-red-500 q-mr-sm', remove='text-green-500 text-gray-400')

    dir_input.on('change', validate_directory_path)
    # Initial validation if there's a value
    if dir_input.value:
        validate_directory_path()

    ui.button(
        'Browse',
        on_click=lambda: browse_directory_simple(dir_input)
    ).classes('bg-gray-300')

    form_widgets[field_id] = dir_input
    return dir_input


def create_file_input(field_id: str, initial_value: Dict[str, Any], form_widgets: Dict) -> Any:
    """
    Create a file input row with validation and a Browse button.
    Intended to be called inside a `with ui.row().classes('items-center gap-2'):` context.
    """
    from rb.api.models import FileInput
    from frontend.utils.file_browser import browse_file_simple

    file_input = ui.input(
        label='File path',
        placeholder='/path/to/file',
        value=initial_value.get('path', '') if isinstance(initial_value, dict) else ''
    ).classes('flex-1')

    # Add validation feedback
    file_validation_status = ui.icon('').classes('text-gray-400 q-mr-sm')

    def validate_file_path():
        path = file_input.value.strip()
        if not path:
            file_validation_status.name = ''
            return

        try:
            FileInput(path=Path(path))
            file_validation_status.name = 'check_circle'
            file_validation_status.classes('text-green-500 q-mr-sm', remove='text-red-500 text-gray-400')
        except Exception:
            file_validation_status.name = 'error'
            file_validation_status.classes('text-red-500 q-mr-sm', remove='text-green-500 text-gray-400')

    file_input.on('change', validate_file_path)
    # Initial validation if there's a value
    if file_input.value:
        validate_file_path()

    ui.button(
        'Browse',
        on_click=lambda: browse_file_simple(file_input)
    ).classes('bg-gray-300')

    form_widgets[field_id] = file_input
    return file_input

