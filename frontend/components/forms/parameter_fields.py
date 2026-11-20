"""Parameter field builders for numeric, ranged, enum, and text parameters."""

from __future__ import annotations

import logging
from typing import Any

from nicegui import ui
from rb.api.models import (
    EnumParameterDescriptor,
    FloatParameterDescriptor,
    IntParameterDescriptor,
    ParameterSchema,
    RangedFloatParameterDescriptor,
    RangedIntParameterDescriptor,
    TextParameterDescriptor,
)

from frontend.utils import select as safe_select
from frontend.utils.image_archive_validation import (
    fetch_archive_labels,
    use_archive_label_picker,
)

logger = logging.getLogger(__name__)


def _is_ranged_float_descriptor(desc: Any) -> bool:
    return isinstance(desc, RangedFloatParameterDescriptor) or (
        isinstance(desc, dict)
        and (desc.get("parameter_type") or desc.get("parameterType")) == "ranged_float"
    )


def _get_ranged_float_values(desc: Any) -> tuple[float, float, float]:
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


def _get_ranged_int_values(desc: Any) -> tuple[int, int, int]:
    if isinstance(desc, RangedIntParameterDescriptor):
        return (desc.range.min, desc.range.max, desc.default)
    r = desc.get("range", {})
    return (int(r.get("min", 0)), int(r.get("max", 100)), int(desc.get("default", 0)))


async def create_parameter_field(
    param_schema: ParameterSchema | dict[str, Any],
    form_widgets: dict[str, Any],
    initial_values: dict[str, Any],
    endpoint: str | None = None,
) -> None:
    """Render a parameter input widget (number, slider, enum select, or text)."""
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
            text_value = (
                str(initial_value)
                if initial_value is not None
                else param_descriptor.default
            )
            if use_archive_label_picker(endpoint, param_id):
                labels = fetch_archive_labels()
                form_widgets[param_id] = safe_select(
                    options=labels,
                    value=text_value if text_value in labels else None,
                    with_input=True,
                    clearable=True,
                ).classes("w-full")
            else:
                form_widgets[param_id] = ui.input(value=text_value).classes("w-full")
