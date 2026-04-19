"""
Form Handlers

This module provides functions for handling form submission, validation,
and data collection. It works with form widgets to extract values and
validate them against TaskSchema definitions.
"""

import logging
from nicegui import ui
from typing import Callable, Dict, Optional
from pathlib import Path
import sys

# Add backend models to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from rb.api.models import TaskSchema
from frontend.utils.validators import validate_form_data
from frontend.utils.error_handling import handle_validation_error, show_error_to_user

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def collect_form_data(
    schema_dict: Dict,
    form_widgets: Dict,
    initial_inputs: Optional[Dict] = None,
) -> Dict:
    """
    Collect data from form widgets.
    
    This function iterates through all form widgets and extracts their values,
    formatting them according to the schema requirements. Handles both
    regular widgets and reactive refs (ui.ref).
    
    Args:
        schema_dict (Dict): Schema dictionary containing inputs and parameters
        form_widgets (Dict): Dictionary of form widgets keyed by field/param ID
    
    Returns:
        Dict: Form data dictionary with structure:
            {
                'inputs': {key: {'path': value} or {'text': value}, ...},
                'parameters': {key: value, ...}
            }
    
    Tips:
    - Reactive refs (ui.ref) are accessed via .value property
    - Regular widgets are accessed via .value property
    - Input types determine the wrapper format (path vs text)
    """
    logger.debug("Collecting form data from widgets")
    inputs_data = {}
    parameters_data = {}
    
    # Collect inputs
    inputs = schema_dict.get('inputs', [])
    for input_schema in inputs:
        field_id = input_schema['key']
        widget = form_widgets.get(field_id)
        if widget:
            input_type = input_schema.get('inputType')
            
            # Handle InputType enum or string
            if isinstance(input_type, str):
                input_type_str = input_type
            else:
                input_type_str = input_type.value if hasattr(input_type, 'value') else str(input_type)
            
            # Handle both ui.ref and regular widgets
            # ui.ref is a function, not a type, so we check by attribute
            if hasattr(widget, 'value'):
                value = widget.value
            else:
                # Fallback: try to get value attribute directly
                value = getattr(widget, 'value', None)
            
            if input_type_str in ['directory', 'file']:
                inputs_data[field_id] = {'path': value}
            elif input_type_str in ['text', 'textarea']:
                inputs_data[field_id] = {'text': value}
            else:
                inputs_data[field_id] = value
    
    # Collect parameters
    parameters = schema_dict.get('parameters', [])
    for param_schema in parameters:
        param_id = param_schema['key']
        widget = form_widgets.get(param_id)
        if widget:
            # Handle enum parameters (stored as dict with widget and label_to_key mapping)
            if isinstance(widget, dict) and 'widget' in widget and 'label_to_key' in widget:
                selected_label = widget['widget'].value
                label_to_key = widget['label_to_key']
                # Convert selected label back to key
                parameters_data[param_id] = label_to_key.get(selected_label, selected_label)
            # Handle both ui.ref and regular widgets
            # ui.ref is a function, not a type, so we check by attribute
            elif hasattr(widget, 'value'):
                parameters_data[param_id] = widget.value
            else:
                parameters_data[param_id] = getattr(widget, 'value', None)
    
    # Re-inject pipeline-only keys from initial_values (not in public schema → no widgets).
    schema_input_keys = {inp['key'] for inp in schema_dict.get('inputs', [])}
    if initial_inputs:
        for k, v in initial_inputs.items():
            if k not in schema_input_keys and k not in inputs_data:
                inputs_data[k] = v
                logger.debug("Merged pipeline input from initial_values: %s", k)

    logger.debug("Form data collection complete: %d inputs, %d parameters", len(inputs_data), len(parameters_data))
    return {
        'inputs': inputs_data,
        'parameters': parameters_data
    }


def validate_form(
    task_schema: TaskSchema,
    form_widgets: Dict,
    initial_inputs: Optional[Dict] = None,
    endpoint: Optional[str] = None,
) -> tuple[bool, Dict]:
    """
    Validate form data using Pydantic models.
    
    This function collects form data and validates it against the TaskSchema
    using the validation utilities. Returns validation result and errors.
    
    Args:
        task_schema (TaskSchema): Schema to validate against
        form_widgets (Dict): Dictionary of form widgets to collect data from
        initial_inputs (Optional[Dict]): Merged pipeline inputs not represented as widgets
        endpoint (Optional[str]): Task endpoint for :func:`validate_form_data` (e.g. image-folder checks)
    
    Returns:
        tuple[bool, Dict]: A tuple containing:
            - bool: True if validation passes, False otherwise
            - Dict: Dictionary of validation errors (empty if validation passes)
    
    Tips:
    - Uses validate_form_data utility for validation
    - Errors dictionary maps field names to error messages
    - User notification should be shown on validation failure
    """
    logger.debug("Validating form data")
    form_data = collect_form_data(task_schema.model_dump(), form_widgets, initial_inputs)
    validation_result = validate_form_data(form_data, task_schema, endpoint=endpoint)
    
    if not validation_result['is_valid']:
        errors = validation_result.get('errors', {})
        logger.warning("Form validation failed with %d errors", len(errors))
        return False, errors
    
    logger.debug("Form validation passed")
    return True, {}


async def handle_form_submit(
    task_schema: TaskSchema,
    form_widgets: Dict,
    onSubmit: Callable,
    initial_inputs: Optional[Dict] = None,
    endpoint: Optional[str] = None,
) -> bool:
    """
    Handle form submission.
    
    This function validates the form data, collects values from all widgets,
    and calls the onSubmit callback with the validated data.
    
    Args:
        task_schema (TaskSchema): Schema used for validation
        form_widgets (Dict): Dictionary of form widgets to collect data from
        onSubmit (Callable): Callback function to call with validated form data
        initial_inputs (Optional[Dict]): Extra inputs merged at collection time
        endpoint (Optional[str]): Task endpoint for validators (e.g. image-folder checks)
    
    Returns:
        bool: True if job was submitted, False if validation/collection failed or error (caller may re-enable submit button)
    
    Tips:
    - Validation must pass before onSubmit is called
    - Form data is collected from all widgets in form_widgets
    - Validation errors are shown as UI notifications
    """
    logger.info("Handling form submission")
    
    try:
        # Validate form
        is_valid, errors = validate_form(task_schema, form_widgets, initial_inputs, endpoint=endpoint)
        if not is_valid:
            logger.warning("Form validation failed with %d errors", len(errors))
            handle_validation_error(errors, "Form submission validation")
            return False
        
        # Collect form data
        logger.debug("Collecting form data from widgets")
        try:
            form_data = collect_form_data(task_schema.model_dump(), form_widgets, initial_inputs)
            logger.debug("Form data collected: %d inputs, %d parameters", len(form_data.get('inputs', {})), len(form_data.get('parameters', {})))
        except Exception as e:
            error_msg = f'Failed to collect form data: {str(e)}'
            logger.error(error_msg, exc_info=True)
            show_error_to_user(error_msg)
            return False
        
        # Call submit callback
        if onSubmit:
            try:
                logger.info("Calling onSubmit callback")
                result = await onSubmit(form_data)
                # Only explicit True means success (disable Submit Job). Callbacks must
                # ``return await submit_form(...)`` so False (e.g. case notes cancelled) is not
                # coerced to None and mistaken for success by an ``else True`` fallback.
                return result is True
            except Exception as e:
                error_msg = f'Form submission failed: {str(e)}'
                logger.error(error_msg, exc_info=True)
                show_error_to_user(error_msg)
                return False
        else:
            logger.warning("No onSubmit callback provided")
            show_error_to_user("Form submission handler not configured")
            return False
    except Exception as e:
        error_msg = f'Unexpected error during form submission: {str(e)}'
        logger.error(error_msg, exc_info=True)
        show_error_to_user(error_msg)
        return False
