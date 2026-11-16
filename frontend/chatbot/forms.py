"""NiceGUI form wrapper for chatbot tool input schemas."""

from collections.abc import Callable
import logging

from nicegui import ui
from rb.api.models import RequestBody, TaskSchema

from frontend.components.forms import FormGenerator
from frontend.utils import validate_request_body

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _validate_or_raise(form_data: dict, schema: TaskSchema, endpoint: str) -> RequestBody:
    validated = validate_request_body(form_data, schema, endpoint)
    if isinstance(validated, RequestBody):
        return validated
    error_info = (
        validated.get("errors") if isinstance(validated, dict) else "Unknown error"
    )
    raise ValueError(f"Validation failed: {error_info}")


async def create_input_form(
    task_schema: TaskSchema,
    endpoint: str,
    initial_values: dict | None = None,
    on_submit: Callable | None = None,
    on_cancel: Callable | None = None,
    container: ui.element | None = None,
):
    """
    Create input form card using FormGenerator. Returns the created card element.
    """
    with container or ui.column():
        # Match assistant message chrome (subtle zinc ring, not heavy indigo border)
        form_card = ui.card().classes(
            "w-full max-w-full min-w-0 text-sm "
            "bg-white ring-1 ring-zinc-200 rounded-2xl rounded-tl-none shadow-sm "
            "border-0 rb-form-wrapper !p-0"
        )
    with form_card:
        async def handle_submit(form_data: dict):
            if on_submit:
                body = _validate_or_raise(form_data, task_schema, endpoint)
                return await on_submit(
                    body, endpoint=endpoint, task_schema=task_schema, form_element=form_card
                )

        await FormGenerator().generate_form(
            schema=task_schema.model_dump(),
            container=form_card,
            initial_values=initial_values,
            on_submit=handle_submit,
            on_cancel=on_cancel,
            compact=True,
            endpoint=endpoint,
        )
    return form_card
