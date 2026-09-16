import logging
from pathlib import Path
from typing import Any

from nicegui import ui
from rb.api.models import (
    DirectoryInput,
    EnumParameterDescriptor,
    FileInput,
    FloatParameterDescriptor,
    InputSchema,
    InputType,
    IntParameterDescriptor,
    ParameterSchema,
    RangedFloatParameterDescriptor,
    RangedIntParameterDescriptor,
    TextParameterDescriptor,
)

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.design_tokens import Design
from frontend.utils import (
    browse_directory_simple,
    browse_file_simple,
    get_active_case,
    maybe_autofill_output_dir_field,
    maybe_autofill_ufdr_mount_name_field,
)
from frontend.utils import (
    select as safe_select,
)
from frontend.utils.validators import _coerce_input_type

logger = logging.getLogger(__name__)


def _field_input_type(input_schema: InputSchema | dict) -> InputType | None:
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
    input_schema: InputSchema,
    form_widgets: dict,
    initial_values: dict,
    autofill_output_key: str | None = None,
    autofill_ufdr_mount_key: str | None = None,
) -> None:
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


async def create_parameter_field(
    param_schema: ParameterSchema | dict, form_widgets: dict, initial_values: dict
) -> None:
    if isinstance(param_schema, dict):
        param_id = param_schema.get("key", "")
        label = param_schema.get("label", param_id)
        subtitle = param_schema.get("subtitle") or ""
        param_descriptor = param_schema.get("value", {})
    else:
        param_id = param_schema.key
        label = param_schema.label
        subtitle = param_schema.subtitle or ""
        param_descriptor = param_schema.value

    default_val = (
        param_descriptor.get("default")
        if isinstance(param_descriptor, dict)
        else getattr(param_descriptor, "default", None)
    )
    initial_value = initial_values.get(param_id, default_val)

    with ui.column().classes("gap-2"):
        ui.label(label).classes("font-semibold")
        if subtitle:
            ui.label(subtitle).classes("text-sm text-zinc-500")

        if _is_ranged_float_descriptor(param_descriptor):
            rmin, rmax, rdefault = _get_ranged_float_values(param_descriptor)
            val = float(initial_value if initial_value is not None else rdefault)
            form_widgets[param_id] = ui.number(
                value=max(rmin, min(rmax, val)),
                min=rmin,
                max=rmax,
                step=0.05,
                format="%.2f",
            ).classes("w-full")
        elif _is_ranged_int_descriptor(param_descriptor):
            rmin, rmax, rdefault = _get_ranged_int_values(param_descriptor)
            val = int(initial_value if initial_value is not None else rdefault)
            form_widgets[param_id] = ui.number(
                value=max(rmin, min(rmax, val)), min=rmin, max=rmax, step=1, format="%d"
            ).classes("w-full")
        elif isinstance(param_descriptor, FloatParameterDescriptor):
            form_widgets[param_id] = ui.number(
                value=(
                    float(initial_value)
                    if initial_value is not None
                    else param_descriptor.default
                ),
                format="%.2f",
            ).classes("w-full")
        elif isinstance(param_descriptor, IntParameterDescriptor):
            form_widgets[param_id] = ui.number(
                value=(
                    int(initial_value)
                    if initial_value is not None
                    else param_descriptor.default
                ),
                format="%d",
            ).classes("w-full")
        elif isinstance(param_descriptor, EnumParameterDescriptor):
            options = [
                opt.label or opt.key
                for opt in param_descriptor.enum_vals
                if opt.label or opt.key
            ]
            l2k = {
                (opt.label or opt.key): opt.key for opt in param_descriptor.enum_vals
            }
            k2l = {v: k for k, v in l2k.items()}
            default_label = k2l.get(
                initial_value,
                (
                    initial_value
                    if initial_value in l2k
                    else (
                        k2l.get(param_descriptor.default)
                        or (options[0] if options else "")
                    )
                ),
            )
            form_widgets[param_id] = {
                "widget": safe_select(options, value=default_label).classes("w-full"),
                "label_to_key": l2k,
            }
        elif isinstance(param_descriptor, TextParameterDescriptor):
            form_widgets[param_id] = ui.input(
                value=(
                    str(initial_value)
                    if initial_value is not None
                    else param_descriptor.default
                )
            ).classes("w-full")


def create_directory_input(
    field_id, initial_value, form_widgets, autofill_output_key=None
):
    active_case = get_active_case()
    case_path = active_case.evidencePath if active_case else ""

    val = ""
    if isinstance(initial_value, dict):
        val = str(initial_value.get("path", "") or "").strip()
    elif isinstance(initial_value, str):
        val = initial_value.strip()

    placeholder = case_path or "/path/to/directory"

    with ui.column().classes("w-full min-w-0 gap-1"):
        ui.label("Directory path").classes("text-sm font-medium text-zinc-700")
        with ui.row().classes("w-full min-w-0 items-center gap-2 flex-nowrap"):
            dir_input = (
                ui.input(
                    placeholder=placeholder,
                    value=val,
                )
                .classes("flex-1 min-w-0")
                .props("outlined dense clearable")
            )
            v_icon = ui.icon("").classes("text-zinc-400 shrink-0")

            def validate():
                p = dir_input.value.strip()
                if not p:
                    v_icon.name = ""
                    return
                try:
                    DirectoryInput(path=Path(p))
                    v_icon.name = "check_circle"
                    v_icon.classes(
                        "text-green-500", remove="text-red-500 text-zinc-400"
                    )
                    if autofill_output_key:
                        maybe_autofill_output_dir_field(
                            form_widgets, autofill_output_key, p
                        )
                except UI_RENDER_ERRORS:
                    v_icon.name = "error"
                    v_icon.classes(
                        "text-red-500", remove="text-green-500 text-zinc-400"
                    )

            def clear_path():
                dir_input.set_value("")
                validate()

            dir_input.on("change", validate)
            if val:
                validate()

            ui.button("Clear", on_click=clear_path).classes(
                f"{Design.BTN_MEDIUM_GRAY} shrink-0"
            )
            ui.button(
                "Browse",
                on_click=lambda: browse_directory_simple(
                    dir_input,
                    initial_path=dir_input.value.strip() or case_path or None,
                    on_after_select=validate,
                ),
            ).classes(f"{Design.BTN_MEDIUM_GRAY} shrink-0")
    form_widgets[field_id] = dir_input


def create_file_input(field_id, initial_value, form_widgets, autofill_mount_key=None):
    active_case = get_active_case()
    default_path = active_case.evidencePath if active_case else ""

    val = ""
    if isinstance(initial_value, dict):
        val = initial_value.get("path", "")
    elif isinstance(initial_value, str):
        val = initial_value

    with ui.column().classes("w-full min-w-0 gap-1"):
        ui.label("File path").classes("text-sm font-medium text-zinc-700")
        with ui.row().classes("w-full min-w-0 items-center gap-2 flex-nowrap"):
            file_input = (
                ui.input(
                    placeholder="/path/to/file",
                    value=val,
                )
                .classes("flex-1 min-w-0")
                .props("outlined dense")
            )
            v_icon = ui.icon("").classes("text-zinc-400 shrink-0")

            def validate():
                p = file_input.value.strip()
                if not p:
                    v_icon.name = ""
                    return
                try:
                    FileInput(path=Path(p))
                    v_icon.name = "check_circle"
                    v_icon.classes(
                        "text-green-500", remove="text-red-500 text-zinc-400"
                    )
                    if autofill_mount_key:
                        maybe_autofill_ufdr_mount_name_field(
                            form_widgets, autofill_mount_key, p
                        )
                except UI_RENDER_ERRORS:
                    v_icon.name = "error"
                    v_icon.classes(
                        "text-red-500", remove="text-green-500 text-zinc-400"
                    )

            file_input.on("change", validate)
            if file_input.value:
                validate()
            ui.button(
                "Browse",
                on_click=lambda: browse_file_simple(
                    file_input,
                    initial_path=default_path or None,
                    on_after_select=validate,
                ),
            ).classes(Design.BTN_MEDIUM_GRAY)
    form_widgets[field_id] = file_input


def _is_ranged_float_descriptor(desc: Any) -> bool:
    return isinstance(desc, RangedFloatParameterDescriptor) or (
        isinstance(desc, dict)
        and (desc.get("parameter_type") or desc.get("parameterType")) == "ranged_float"
    )


def _get_ranged_float_values(desc: Any) -> tuple:
    if isinstance(desc, RangedFloatParameterDescriptor):
        return (float(desc.range.min), float(desc.range.max), float(desc.default))
    r = desc.get("range", {})
    return (
        float(r.get("min", 0)),
        float(r.get("max", 1)),
        float(desc.get("default", 0.5)),
    )


def _is_ranged_int_descriptor(desc: Any) -> bool:
    return isinstance(desc, RangedIntParameterDescriptor) or (
        isinstance(desc, dict)
        and (desc.get("parameter_type") or desc.get("parameterType")) == "ranged_int"
    )


def _get_ranged_int_values(desc: Any) -> tuple:
    if isinstance(desc, RangedIntParameterDescriptor):
        return (int(desc.range.min), int(desc.range.max), int(desc.default))
    r = desc.get("range", {})
    return (int(r.get("min", 0)), int(r.get("max", 100)), int(desc.get("default", 0)))
