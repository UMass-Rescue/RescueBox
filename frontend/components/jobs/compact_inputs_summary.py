import logging
from nicegui import ui
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_compact_inputs_summary(container: ui.element, task_schema: Any, request_body: Any) -> None:
    """
    Render a compact summary of inputs and parameters inside `container`.
    """
    logger.debug("Rendering compact inputs summary (component)")
    with container:
        with ui.expansion('📋 View Inputs & Parameters', icon='description').classes('w-full mb-4'):
            with ui.column().classes('gap-3 p-4 bg-gray-50 rounded'):
                # Inputs
                if getattr(task_schema, 'inputs', None):
                    ui.label('Inputs').classes('font-semibold text-lg')
                    for input_schema in task_schema.inputs:
                        field_id = input_schema.key
                        field_input = request_body.inputs.get(field_id)

                        with ui.row().classes('items-start gap-2'):
                            ui.label(input_schema.label).classes('w-32 font-semibold text-sm')

                            if field_input:
                                input_root = field_input.root if hasattr(field_input, 'root') else field_input

                                if hasattr(input_root, 'path'):
                                    path_str = str(input_root.path)
                                    display_path = path_str if len(path_str) < 80 else path_str[:77] + '...'
                                    ui.label(display_path).classes('flex-1 text-sm font-mono text-gray-700')
                                elif hasattr(input_root, 'text'):
                                    text = input_root.text
                                    first_line = text.split('\n')[0] if '\n' in text else text
                                    display_text = first_line if len(first_line) < 100 else first_line[:97] + '...'
                                    ui.label(display_text).classes('flex-1 text-sm text-gray-700')
                                else:
                                    ui.label(str(input_root)).classes('flex-1 text-sm text-gray-700')
                            else:
                                ui.label('(not provided)').classes('flex-1 text-sm text-gray-400 italic')

                # Parameters
                if getattr(task_schema, 'parameters', None):
                    ui.label('Parameters').classes('font-semibold text-lg mt-2')
                    for param_schema in task_schema.parameters:
                        param_id = param_schema.key
                        param_value = request_body.parameters.get(param_id)

                        with ui.row().classes('items-center gap-2'):
                            ui.label(param_schema.label).classes('w-32 font-semibold text-sm')
                            ui.label(str(param_value) if param_value is not None else '(not provided)').classes('flex-1 text-sm text-gray-700')

    logger.debug("Compact inputs summary (component) rendered")

