from nicegui import ui

from frontend.utils import handle_validation_error, show_error_to_user

from . import form_generator
from .dialogs import show_case_notes_dialog
from .field_builders import (
    create_directory_input,
    create_file_input,
    create_input_field,
    create_parameter_field,
)
from .form_generator import (
    FormGenerator,
    collect_form_data,
    handle_form_submit,
    render_form_actions,
    validate_form,
)

# Backward-compatible alias (prefer ``form_generator`` in new code).
form_handlers = form_generator

__all__ = [
    "FormGenerator",
    "collect_form_data",
    "create_directory_input",
    "create_file_input",
    "create_input_field",
    "create_parameter_field",
    "form_generator",
    "form_handlers",
    "handle_form_submit",
    "handle_validation_error",
    "render_form_actions",
    "show_case_notes_dialog",
    "show_error_to_user",
    "ui",
    "validate_form",
]
