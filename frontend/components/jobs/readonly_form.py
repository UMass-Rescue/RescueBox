import logging
from nicegui import ui
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _readonly_value_block(value: str, *, monospace: bool = False) -> None:
    """Full-width read-only field that wraps long lines (paths, text) instead of horizontal scroll."""
    extra = "font-mono text-xs" if monospace else "text-sm"
    ui.textarea(
        label="",
        value=value,
    ).classes(f"w-full min-w-0 max-w-full {extra} break-all").props(
        "readonly outlined dense autogrow"
    )


def render_readonly_form(container: ui.element, task_schema: Any, request_body: Any) -> None:
    """
    Render read-only form for job inputs and parameters inside `container`.

    Uses full container width with stacked label + wrapping textarea so long paths
    do not require horizontal scrolling in a narrow input.
    """
    logger.debug("Rendering read-only form (component)")
    with container:
        ui.label("Request Inputs and Parameters").classes("text-xl font-bold mt-6")

        with ui.column().classes("gap-4 mt-4 w-full min-w-0 max-w-full"):
            # Inputs
            if getattr(task_schema, "inputs", None):
                ui.label("Inputs").classes("font-semibold text-lg")
                for input_schema in task_schema.inputs:
                    field_id = input_schema.key
                    field_input = request_body.inputs.get(field_id)

                    with ui.column().classes("w-full min-w-0 max-w-full gap-1"):
                        ui.label(input_schema.label).classes(
                            "font-semibold text-sm text-zinc-800"
                        )

                        if field_input:
                            input_root = (
                                field_input.root
                                if hasattr(field_input, "root")
                                else field_input
                            )

                            if hasattr(input_root, "path"):
                                _readonly_value_block(
                                    str(input_root.path), monospace=True
                                )
                            elif hasattr(input_root, "text"):
                                ui.textarea(
                                    label="",
                                    value=input_root.text,
                                ).classes(
                                    "w-full min-w-0 max-w-full text-sm break-words whitespace-pre-wrap"
                                ).props("readonly outlined dense autogrow")
                            else:
                                _readonly_value_block(str(input_root), monospace=True)
                        else:
                            ui.label("(not provided)").classes(
                                "text-sm text-zinc-400 italic"
                            )

            # Parameters
            if getattr(task_schema, "parameters", None):
                ui.label("Parameters").classes("font-semibold text-lg mt-4")
                for param_schema in task_schema.parameters:
                    param_id = param_schema.key
                    param_value = request_body.parameters.get(param_id)

                    with ui.column().classes("w-full min-w-0 max-w-full gap-1"):
                        ui.label(param_schema.label).classes(
                            "font-semibold text-sm text-zinc-800"
                        )
                        if param_value is None:
                            ui.label("(not provided)").classes(
                                "text-sm text-zinc-400 italic"
                            )
                        else:
                            _readonly_value_block(str(param_value))

    logger.debug("Read-only form (component) rendered")
