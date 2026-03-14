"""
Parameter Field Builder

This module provides functions for creating parameter form fields.
"""

import logging
from nicegui import ui
from typing import Dict
from pathlib import Path
import sys

# Add backend models to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

from rb.api.models import (
    ParameterSchema,
    RangedFloatParameterDescriptor,
    RangedIntParameterDescriptor,
    FloatParameterDescriptor,
    IntParameterDescriptor,
    EnumParameterDescriptor,
    TextParameterDescriptor,
)

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def create_parameter_field(
    param_schema: ParameterSchema,
    form_widgets: Dict,
    initial_values: Dict
) -> None:
    """
    Create a parameter field from ParameterSchema.

    This function creates appropriate UI controls based on parameter descriptor type:
    - RangedFloatParameterDescriptor: Slider with reactive value label
    - RangedIntParameterDescriptor: Slider with reactive value label
    - FloatParameterDescriptor: Number input with decimal formatting
    - IntParameterDescriptor: Number input with integer formatting
    - EnumParameterDescriptor: Dropdown select with options
    - TextParameterDescriptor: Text input field

    The widget (or reactive ref) is stored for form data collection.

    Args:
        param_schema (ParameterSchema): Schema defining the parameter field
        form_widgets (Dict): Dictionary to store widget references (keyed by param_id)
        initial_values (Dict): Dictionary containing initial form values

    Returns:
        None: Field is added directly to the current UI context

    Tips:
    - Sliders use ui.ref for reactive state management (NiceGUI binding)
    - Initial values come from initial_values or parameter default
    - Reactive refs are stored for sliders, regular widgets for others
    """
    param_id = param_schema.key
    label = param_schema.label
    subtitle = param_schema.subtitle or ''
    param_descriptor = param_schema.value

    logger.debug("Creating parameter field: %s (descriptor type: %s)", param_id, type(param_descriptor).__name__)

    initial_value = initial_values.get(param_id, getattr(param_descriptor, 'default', None))

    with ui.column().classes('gap-2'):
        if subtitle:
            ui.label(label).classes('font-semibold')
            ui.label(subtitle).classes('text-sm text-gray-500')
        else:
            ui.label(label).classes('font-semibold')

        if isinstance(param_descriptor, RangedFloatParameterDescriptor):
            initial = initial_value if initial_value is not None else param_descriptor.default
            try:
                from frontend.components.forms.fields.parameter_widgets import create_ranged_float_widget
                create_ranged_float_widget(param_id, param_descriptor, float(initial), form_widgets)
            except Exception:
                # Create slider with initial value and a value label updated via event handler
                with ui.row().classes('items-center gap-4'):
                    slider = ui.slider(
                        min=param_descriptor.range.min,
                        max=param_descriptor.range.max,
                        step=0.01,
                        value=float(initial)
                    ).classes('flex-1')

                    # Label showing formatted slider value
                    value_label = ui.label(f'{float(initial):.2f}').classes('w-16 text-right')

                    # Update label when slider value changes
                    def _on_slider_update(e):
                        try:
                            # event args may contain the new value in different shapes
                            new_val = e.args[0] if e.args else slider.value
                            value_label.text = f'{float(new_val):.2f}'
                        except Exception:
                            try:
                                value_label.text = str(slider.value)
                            except Exception:
                                value_label.text = ''

                    slider.on('update:modelValue', _on_slider_update)

                    # Store the slider widget for form collection (value read from slider.value)
                    form_widgets[param_id] = slider

        elif isinstance(param_descriptor, RangedIntParameterDescriptor):
            initial = initial_value if initial_value is not None else param_descriptor.default
            try:
                from frontend.components.forms.fields.parameter_widgets import create_ranged_int_widget
                create_ranged_int_widget(param_id, param_descriptor, int(initial), form_widgets)
            except Exception:
                # Create integer slider with initial value and update label on change
                with ui.row().classes('items-center gap-4'):
                    slider = ui.slider(
                        min=param_descriptor.range.min,
                        max=param_descriptor.range.max,
                        step=1,
                        value=int(initial)
                    ).classes('flex-1')

                    value_label = ui.label(str(int(initial))).classes('w-16 text-right')

                    def _on_int_slider_update(e):
                        try:
                            new_val = e.args[0] if e.args else slider.value
                            value_label.text = str(int(new_val))
                        except Exception:
                            try:
                                value_label.text = str(int(slider.value))
                            except Exception:
                                value_label.text = ''

                    slider.on('update:modelValue', _on_int_slider_update)
                    form_widgets[param_id] = slider

        elif isinstance(param_descriptor, FloatParameterDescriptor):
            initial_num = float(initial_value) if initial_value is not None else param_descriptor.default
            try:
                from frontend.components.forms.fields.parameter_widgets import create_number_input
                create_number_input(param_id, initial_num, '%.2f', form_widgets)
            except Exception:
                number_input = ui.number(
                    label='',
                    value=initial_num,
                    format='%.2f'
                ).classes('w-full')
                form_widgets[param_id] = number_input

        elif isinstance(param_descriptor, IntParameterDescriptor):
            initial_num = int(initial_value) if initial_value is not None else param_descriptor.default
            try:
                from frontend.components.forms.fields.parameter_widgets import create_number_input
                create_number_input(param_id, initial_num, '%d', form_widgets)
            except Exception:
                number_input = ui.number(
                    label='',
                    value=initial_num,
                    format='%d'
                ).classes('w-full')
                form_widgets[param_id] = number_input

        elif isinstance(param_descriptor, EnumParameterDescriptor):
            # Create mapping from label to key for form submission
            # Store both the select widget and the label-to-key mapping
            label_to_key = {}
            key_to_label = {}
            options = []

            for opt in param_descriptor.enum_vals:
                if opt.label or opt.key:
                    display_label = opt.label or opt.key
                    options.append(display_label)
                    label_to_key[display_label] = opt.key
                    key_to_label[opt.key] = display_label

            # Determine the default label to display
            default_label = None

            # If initial_value is provided, use it (could be key or label)
            if initial_value is not None:
                # Check if initial_value is a key
                if initial_value in key_to_label:
                    default_label = key_to_label[initial_value]
                # Check if initial_value is already a label
                elif initial_value in label_to_key:
                    default_label = initial_value

            # If no initial_value match, find the default label from the default key
            if default_label is None:
                default_key = param_descriptor.default
                if default_key in key_to_label:
                    default_label = key_to_label[default_key]

            # If still no match found, use first option
            if default_label is None and options:
                default_label = options[0]

            try:
                from frontend.components.forms.fields.parameter_widgets import create_enum_select
                create_enum_select(param_id, options, default_label, form_widgets, label_to_key=label_to_key)
            except Exception:
                from frontend.utils.nicegui_compat import select as safe_select
                select = safe_select(
                    options,
                    label='',
                    value=default_label
                ).classes('w-full')  # type: ignore[call-arg]

                # Store both the select widget and the mapping for form collection
                form_widgets[param_id] = {
                    'widget': select,
                    'label_to_key': label_to_key
                }

        elif isinstance(param_descriptor, TextParameterDescriptor):
            try:
                from frontend.components.forms.fields.parameter_widgets import create_text_input
                create_text_input(param_id, initial_value if initial_value is not None else param_descriptor.default, form_widgets)
            except Exception:
                text_input = ui.input(
                    label='',
                    value=str(initial_value) if initial_value is not None else param_descriptor.default,
                    placeholder='Enter text...'
                ).classes('w-full')
                form_widgets[param_id] = text_input

    logger.debug("Parameter field created: %s", param_id)
