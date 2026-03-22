from typing import Optional, Dict
import logging
from nicegui import ui
from frontend.components.forms.form_generator import FormGenerator
from frontend.utils.validators import validate_request_body
from rb.api.models import TaskSchema, RequestBody

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def create_input_form(task_schema: TaskSchema, endpoint: str, initial_values: Optional[Dict] = None, on_submit: callable = None, on_cancel: callable = None):
    """
    Create input form card using FormGenerator. Returns the created card element.
    """
    # Allow wider form cards so input fields (paths) are not cramped on small screens
    form_card = ui.card().classes('w-full max-w-2xl bg-white border-2 border-blue-500 text-sm')
    with form_card:
        form_generator = FormGenerator()

        async def handle_submit(form_data: dict):
            validated = validate_request_body(form_data, task_schema)
            if not isinstance(validated, RequestBody):
                error_info = validated.get('errors') if isinstance(validated, dict) else "Unknown error"
                raise Exception(f"Validation failed: {error_info}")
            elif on_submit:
                return await on_submit(validated, endpoint, task_schema)

        await form_generator.generate_form(
            schema=task_schema.model_dump(),
            container=form_card,
            initial_values=initial_values,
            onSubmit=handle_submit,
            onCancel=on_cancel,
            compact=True
        )
    return form_card

