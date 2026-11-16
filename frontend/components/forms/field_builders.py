"""Input and parameter field builders for dynamically generated forms."""

from __future__ import annotations

import logging
from typing import Any

from nicegui import ui
from rb.api.models import InputSchema, InputType

from frontend.utils.validators import _coerce_input_type

from .parameter_fields import create_parameter_field
from .path_inputs import create_directory_input, create_file_input

logger = logging.getLogger(__name__)


def _field_input_type(input_schema: InputSchema | dict[str, Any]) -> InputType | None:
    if isinstance(input_schema, dict):
        raw = input_schema.get("inputType") or input_schema.get("input_type")
        if isinstance(raw, InputType):
            return raw
        try:
            return InputType(raw) if raw is not None else None
        except (ValueError, TypeError):
            return None
    return _coerce_input_type(input_schema)


async def create_input_field(
    input_schema: InputSchema | dict[str, Any],
    form_widgets: dict[str, Any],
    initial_values: dict[str, Any],
    autofill_output_key: str | None = None,
    autofill_ufdr_mount_key: str | None = None,
) -> None:
    """Render an input field (directory, file, textarea, or text input) based on schema."""
    if isinstance(input_schema, dict):
        field_id = input_schema.get("key", "")
        label = input_schema.get("label", field_id)
        subtitle = input_schema.get("subtitle") or ""
    else:
        field_id = input_schema.key
        label = input_schema.label
        subtitle = input_schema.subtitle or ""
    input_type = _field_input_type(input_schema)

    with ui.column().classes("gap-2 w-full min-w-0"):
        ui.label(label).classes("font-semibold")
        if subtitle:
            ui.label(subtitle).classes("text-sm text-zinc-500")

        if input_type == InputType.DIRECTORY:
            create_directory_input(
                field_id,
                initial_values.get(field_id, {}),
                form_widgets,
                autofill_output_key,
            )
        elif input_type == InputType.FILE:
            create_file_input(
                field_id,
                initial_values.get(field_id, {}),
                form_widgets,
                autofill_ufdr_mount_key,
            )
        elif input_type == InputType.TEXTAREA:
            form_widgets[field_id] = ui.textarea(
                value=(
                    initial_values.get(field_id, {}).get("text", "")
                    if isinstance(initial_values.get(field_id), dict)
                    else ""
                )
            ).classes("w-full")
        elif input_type == InputType.TEXT:
            form_widgets[field_id] = ui.input(
                value=(
                    initial_values.get(field_id, {}).get("text", "")
                    if isinstance(initial_values.get(field_id), dict)
                    else ""
                )
            ).classes("w-full")


__all__ = [
    "create_directory_input",
    "create_file_input",
    "create_input_field",
    "create_parameter_field",
]
