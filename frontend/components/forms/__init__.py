from nicegui import ui
from .form_generator import FormGenerator, render_form_actions, handle_form_submit, collect_form_data, validate_form
from . import form_generator as form_handlers
from .field_builders import create_input_field, create_parameter_field, create_directory_input, create_file_input
from .dialogs import show_case_notes_dialog
from frontend.utils import handle_validation_error, show_error_to_user

__all__ = [
    'FormGenerator',
    'render_form_actions',
    'handle_form_submit',
    'collect_form_data',
    'create_input_field',
    'create_parameter_field',
    'create_directory_input',
    'create_file_input',
    'show_case_notes_dialog',
    'validate_form',
    'ui',
    'form_handlers',
    'handle_validation_error',
    'show_error_to_user'
]

# Legacy alias for backward compatibility if needed
def create_form(*args, **kwargs):
    """Legacy wrapper for generate_form."""
    generator = FormGenerator()
    # If called in sync context, this won't work well, but generate_form is async
    return generator.generate_form(*args, **kwargs)
