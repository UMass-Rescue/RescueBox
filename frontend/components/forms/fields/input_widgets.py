import logging
from nicegui import ui
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_directory_input(
    field_id: str,
    initial_value: Dict[str, Any],
    form_widgets: Dict,
    autofill_output_key: Optional[str] = None,
) -> Any:
    """
    Full-width directory path field with Browse. Uses an external caption so the control
    spans the form (Quasar ``label=`` on ``ui.input`` keeps the field visually narrow).
    """
    from rb.api.models import DirectoryInput
    from frontend.utils.file_browser import browse_directory_simple

    with ui.column().classes('w-full min-w-0 gap-1'):
        ui.label('Directory path').classes('text-sm font-medium text-gray-700')
        with ui.row().classes('w-full min-w-0 items-center gap-2 flex-nowrap'):
            dir_input = ui.input(
                label='',
                placeholder='/path/to/directory',
                value=initial_value.get('path', '') if isinstance(initial_value, dict) else '',
            ).classes('flex-1 min-w-0').props('outlined dense')

            validation_status = ui.icon('').classes('text-gray-400 shrink-0')

            def validate_directory_path():
                path = dir_input.value.strip()
                if not path:
                    validation_status.name = ''
                    return

                try:
                    DirectoryInput(path=Path(path))
                    validation_status.name = 'check_circle'
                    validation_status.classes('text-green-500', remove='text-red-500 text-gray-400')
                    if autofill_output_key:
                        from frontend.utils.job_form_paths import maybe_autofill_output_dir_field

                        maybe_autofill_output_dir_field(form_widgets, autofill_output_key, path)
                except Exception:
                    validation_status.name = 'error'
                    validation_status.classes('text-red-500', remove='text-green-500 text-gray-400')

            dir_input.on('change', validate_directory_path)
            if dir_input.value:
                validate_directory_path()

            ui.button(
                'Browse',
                on_click=lambda: browse_directory_simple(
                    dir_input, on_after_select=validate_directory_path
                ),
            ).classes('shrink-0 bg-gray-300')

    form_widgets[field_id] = dir_input
    return dir_input


def create_file_input(
    field_id: str,
    initial_value: Dict[str, Any],
    form_widgets: Dict,
    autofill_mount_name_key: Optional[str] = None,
) -> Any:
    """
    Full-width file path field with Browse (same layout as directory input).
    """
    from rb.api.models import FileInput
    from frontend.utils.file_browser import browse_file_simple

    with ui.column().classes('w-full min-w-0 gap-1'):
        ui.label('File path').classes('text-sm font-medium text-gray-700')
        with ui.row().classes('w-full min-w-0 items-center gap-2 flex-nowrap'):
            file_input = ui.input(
                label='',
                placeholder='/path/to/file',
                value=initial_value.get('path', '') if isinstance(initial_value, dict) else '',
            ).classes('flex-1 min-w-0').props('outlined dense')

            file_validation_status = ui.icon('').classes('text-gray-400 shrink-0')

            def validate_file_path():
                path = file_input.value.strip()
                if not path:
                    file_validation_status.name = ''
                    return

                try:
                    FileInput(path=Path(path))
                    file_validation_status.name = 'check_circle'
                    file_validation_status.classes('text-green-500', remove='text-red-500 text-gray-400')
                    if autofill_mount_name_key:
                        from frontend.utils.job_form_paths import (
                            maybe_autofill_ufdr_mount_name_field,
                        )

                        maybe_autofill_ufdr_mount_name_field(
                            form_widgets, autofill_mount_name_key, path
                        )
                except Exception:
                    file_validation_status.name = 'error'
                    file_validation_status.classes('text-red-500', remove='text-green-500 text-gray-400')

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
    return file_input

