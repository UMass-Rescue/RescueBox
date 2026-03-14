import logging
from nicegui import ui
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_readonly_form(container: ui.element, task_schema: Any, request_body: Any) -> None:
    """
    Render read-only form for job inputs and parameters inside `container`.
    """
    logger.debug("Rendering read-only form (component)")
    with container:
        ui.label('Request Inputs and Parameters').classes('text-xl font-bold mt-6')

        with ui.column().classes('gap-4 mt-4'):
            # Inputs
            if getattr(task_schema, 'inputs', None):
                ui.label('Inputs').classes('font-semibold text-lg')
                for input_schema in task_schema.inputs:
                    field_id = input_schema.key
                    field_input = request_body.inputs.get(field_id)

                    with ui.row().classes('items-center gap-2'):
                        ui.label(input_schema.label).classes('w-32 font-semibold')

                        if field_input:
                            input_root = field_input.root if hasattr(field_input, 'root') else field_input

                            if hasattr(input_root, 'path'):
                                ui.input(
                                    label='',
                                    value=str(input_root.path)
                                ).classes('flex-1').props('readonly')
                            elif hasattr(input_root, 'text'):
                                ui.textarea(
                                    label='',
                                    value=input_root.text
                                ).classes('flex-1').props('readonly')
                            else:
                                ui.input(
                                    label='',
                                    value=str(input_root)
                                ).classes('flex-1').props('readonly')

            # Parameters
            if getattr(task_schema, 'parameters', None):
                ui.label('Parameters').classes('font-semibold text-lg mt-4')
                for param_schema in task_schema.parameters:
                    param_id = param_schema.key
                    param_value = request_body.parameters.get(param_id)

                    with ui.row().classes('items-center gap-2'):
                        ui.label(param_schema.label).classes('w-32 font-semibold')
                        ui.input(
                            label='',
                            value=str(param_value) if param_value is not None else ''
                        ).classes('flex-1').props('readonly')

    logger.debug("Read-only form (component) rendered")

