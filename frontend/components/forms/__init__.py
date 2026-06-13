from nicegui import ui
from .form_generator import (
    FormGenerator,
    render_form_actions,
    handle_form_submit,
    collect_form_data,
    validate_form,
)
from . import form_generator
from .field_builders import (
    create_input_field,
    create_parameter_field,
    create_directory_input,
    create_file_input,
)
from .dialogs import show_case_notes_dialog
from frontend.utils import handle_validation_error, show_error_to_user

# Backward-compatible alias (prefer ``form_generator`` in new code).
form_handlers = form_generator

__all__ = [
    "FormGenerator",
    "render_form_actions",
    "handle_form_submit",
    "collect_form_data",
    "create_input_field",
    "create_parameter_field",
    "create_directory_input",
    "create_file_input",
    "show_case_notes_dialog",
    "validate_form",
    "ui",
    "form_generator",
    "form_handlers",
    "handle_validation_error",
    "show_error_to_user",
]
