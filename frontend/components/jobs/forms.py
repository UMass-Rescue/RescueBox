from __future__ import annotations

import logging
from typing import Any

from nicegui import ui

logger = logging.getLogger(__name__)


def render_compact_inputs_summary(
    container: ui.element, task_schema: Any, request_body: Any
) -> None:
    """
    Render a compact summary of inputs and parameters inside `container`.
    """
    logger.debug("Rendering compact inputs summary (component)")
    with container, ui.expansion("View inputs & parameters").classes("w-full mb-4"):
        with ui.column().classes("gap-3 p-4 bg-zinc-50 rounded"):
            # Inputs
            if getattr(task_schema, "inputs", None):
                ui.label("Inputs").classes("font-semibold text-lg")
                for input_schema in task_schema.inputs:
                    field_id = input_schema.key
                    field_input = request_body.inputs.get(field_id)

                    with ui.row().classes("items-start gap-2"):
                        ui.label(input_schema.label).classes(
                            "w-32 font-semibold text-sm"
                        )

                        if field_input:
                            input_root = (
                                field_input.root
                                if hasattr(field_input, "root")
                                else field_input
                            )

                            if hasattr(input_root, "path"):
                                ui.label(str(input_root.path)).classes(
                                    "flex-1 text-sm font-mono text-zinc-700 break-all"
                                )
                            elif hasattr(input_root, "text"):
                                text = input_root.text
                                first_line = (
                                    text.split("\n")[0] if "\n" in text else text
                                )
                                display_text = first_line
                                ui.label(display_text).classes(
                                    "flex-1 text-sm text-zinc-700"
                                )
                            else:
                                ui.label(str(input_root)).classes(
                                    "flex-1 text-sm text-zinc-700"
                                )
                        else:
                            ui.label("(not provided)").classes(
                                "flex-1 text-sm text-zinc-400 italic"
                            )

            # Parameters
            if getattr(task_schema, "parameters", None):
                ui.label("Parameters").classes("font-semibold text-lg mt-2")
                for param_schema in task_schema.parameters:
                    param_id = param_schema.key
                    param_value = request_body.parameters.get(param_id)

                    with ui.row().classes("items-center gap-2"):
                        ui.label(param_schema.label).classes(
                            "w-32 font-semibold text-sm"
                        )
                        ui.label(
                            str(param_value)
                            if param_value is not None
                            else "(not provided)"
                        ).classes("flex-1 text-sm text-zinc-700")

    logger.debug("Compact inputs summary (component) rendered")


def _readonly_value_block(value: str, *, monospace: bool = False) -> None:
    """Full-width read-only field that wraps long lines (paths, text) instead of horizontal scroll."""
    extra = "font-mono text-xs" if monospace else "text-sm"
    ui.textarea(
        label="",
        value=value,
    ).classes(
        f"w-full min-w-0 max-w-full {extra} break-all"
    ).props("readonly outlined dense autogrow")


def render_readonly_form(
    container: ui.element, task_schema: Any, request_body: Any
) -> None:
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
