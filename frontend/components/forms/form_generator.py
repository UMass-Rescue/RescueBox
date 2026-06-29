import logging
from typing import Callable

from nicegui import ui
from rb.api.models import TaskSchema
from frontend.design_tokens import Design
from frontend.utils.paths import apply_ufdr_mount_autofill_after_inputs_built
from frontend.utils.ui import handle_validation_error, show_error_to_user
from frontend.utils.validators import (
    paired_output_directory_field_id,
    paired_ufdr_mount_folder_field_id,
    paired_ufdr_mount_name_field_id,
    validate_form_data,
)

from .field_builders import create_input_field, create_parameter_field
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)


def render_form_actions(
    container: ui.element,
    on_cancel: Callable,
    on_submit: Callable,
    compact: bool = False,
):
    with container:
        with ui.row().classes(f"{'mt-3' if compact else 'mt-6'} gap-2"):
            ui.space()

            def _cancel_wrapper():
                outer = getattr(container, "_outer_form_container", None)
                if outer:
                    try:
                        outer.delete()
                    except UI_RENDER_ERRORS:
                        pass
                    return
                on_cancel()

            ui.button("Cancel", color=None, on_click=_cancel_wrapper).classes(
                Design.BTN_MEDIUM_GRAY
            )

            btn_ref = [None]

            async def _submit_wrapper():
                btn = btn_ref[0]
                if not btn:
                    return
                btn.props["loading"] = True
                try:
                    if await on_submit() is True:
                        btn.disable()
                finally:
                    btn.props["loading"] = False

            submit_btn = ui.button(
                "Submit Job", color=None, on_click=_submit_wrapper
            ).classes("rb-brand-primary text-white rounded-xl")
            btn_ref[0] = submit_btn
            return submit_btn


class FormGenerator:
    def __init__(self):
        self.form_data = {}
        self.form_widgets = {}

    def reset(self) -> None:
        """Clear collected form state and widget references."""
        self.form_data = {}
        self.form_widgets = {}

    async def generate_form(
        self,
        schema,
        container,
        initial_values=None,
        on_submit=None,
        on_cancel=None,
        compact=False,
        endpoint=None,
    ):
        if isinstance(schema, dict):
            # Normalization logic
            params = schema.get("parameters")
            if isinstance(params, dict):
                schema["parameters"] = [
                    {
                        "key": k,
                        "label": v.get("label", k.replace("_", " ").title()),
                        "subtitle": v.get("subtitle", ""),
                        "value": v.get("value", v),
                    }
                    for k, v in params.items()
                ]
            schema = TaskSchema(**schema)

        self.form_data = initial_values or {}
        self.form_widgets = {}

        with container:
            with ui.column().classes(
                f"w-full min-w-0 max-w-full {'p-3 space-y-2' if compact else 'p-6 space-y-4'}"
            ):
                ui.label("Input form").classes(
                    "text-xl font-bold" if not compact else "text-lg font-bold"
                )

                if schema.inputs:
                    ui.label("Inputs").classes(
                        "font-semibold text-lg mt-4"
                        if not compact
                        else "font-semibold text-base mt-2"
                    )
                    inputs_list = list(schema.inputs)
                    for idx, inp in enumerate(inputs_list):
                        await create_input_field(
                            inp,
                            self.form_widgets,
                            self.form_data.get("inputs", {}),
                            paired_output_directory_field_id(inputs_list, idx),
                            paired_ufdr_mount_name_field_id(inputs_list, idx),
                        )
                    for idx in range(len(inputs_list)):
                        mount_folder_id = paired_ufdr_mount_folder_field_id(
                            inputs_list, idx
                        )
                        if mount_folder_id:
                            try:
                                apply_ufdr_mount_autofill_after_inputs_built(
                                    self.form_widgets,
                                    "ufdr_file",
                                    mount_folder_id,
                                )
                            except UI_RENDER_ERRORS:
                                pass
                            break

                if schema.parameters:
                    ui.label("Parameters").classes(
                        "font-semibold text-lg mt-4"
                        if not compact
                        else "font-semibold text-base mt-2"
                    )
                    for param in schema.parameters:
                        await create_parameter_field(
                            param,
                            self.form_widgets,
                            self.form_data.get("parameters", {}),
                        )

                def _on_cancel():
                    if on_cancel:
                        on_cancel()
                    container.clear()

                async def _on_submit():
                    if not on_submit:
                        return False
                    return await handle_form_submit(
                        schema, self.form_widgets, on_submit, endpoint=endpoint
                    )

                action_col = ui.column()
                setattr(action_col, "_outer_form_container", container)
                render_form_actions(action_col, _on_cancel, _on_submit, compact=compact)


async def handle_form_submit(
    schema, widgets, on_submit, initial_inputs=None, endpoint=None
):
    try:
        if on_submit is None:
            show_error_to_user("Form submission handler is not configured")
            return False
        try:
            form_data = collect_form_data(schema.model_dump(), widgets, initial_inputs)
        except UI_RENDER_ERRORS as e:
            show_error_to_user(f"Failed to collect form data: {e}")
            return False

        v_res = validate_form_data(form_data, schema, endpoint)
        if not v_res["is_valid"]:
            handle_validation_error(
                v_res.get("errors", {}), "Form submission validation"
            )
            return False

        res = await on_submit(form_data)
        return res is True
    except UI_RENDER_ERRORS as e:
        show_error_to_user(f"Form submission failed: {e}")
        return False


def collect_form_data(schema_dict, widgets, initial_inputs=None):
    inputs_data = {}
    params_data = {}

    for inp in schema_dict.get("inputs", []):
        fid = inp["key"]
        w = widgets.get(fid)
        if not w:
            continue
        val = getattr(w, "value", None)
        raw_it = inp.get("inputType") or inp.get("input_type")
        if not raw_it:
            inputs_data[fid] = val
            continue
        it = str(raw_it.value if hasattr(raw_it, "value") else raw_it)
        if it in ["directory", "file"]:
            inputs_data[fid] = {"path": val}
        elif it in ["text", "textarea"]:
            inputs_data[fid] = {"text": val}
        elif it == "batchfile":
            inputs_data[fid] = {"files": val if isinstance(val, list) else []}
        elif it == "batchtext":
            inputs_data[fid] = {"texts": val if isinstance(val, list) else []}
        elif it == "batchdirectory":
            inputs_data[fid] = {"directories": val if isinstance(val, list) else []}
        else:
            inputs_data[fid] = val

    for param in schema_dict.get("parameters", []):
        pid = param["key"]
        w = widgets.get(pid)
        if not w:
            continue
        if isinstance(w, dict) and "widget" in w:
            params_data[pid] = w["label_to_key"].get(
                w["widget"].value, w["widget"].value
            )
        else:
            params_data[pid] = getattr(w, "value", None)

    if initial_inputs:
        for k, v in initial_inputs.items():
            if k not in inputs_data:
                inputs_data[k] = v
    return {"inputs": inputs_data, "parameters": params_data}


def validate_form(schema, widgets, initial_inputs=None, endpoint=None):
    form_data = collect_form_data(
        schema.model_dump() if hasattr(schema, "model_dump") else schema,
        widgets,
        initial_inputs,
    )
    v_res = validate_form_data(form_data, schema, endpoint)
    if not v_res["is_valid"]:
        return False, v_res.get("errors", {})
    return True, {}
