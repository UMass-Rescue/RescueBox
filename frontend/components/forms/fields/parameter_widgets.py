import logging
from nicegui import ui
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_ranged_float_widget(param_id: str, descriptor: Any, initial: float, form_widgets: Dict):
    """Create a float slider with label showing formatted value."""
    with ui.row().classes('items-center gap-4'):
        slider = ui.slider(
            min=descriptor.range.min,
            max=descriptor.range.max,
            step=0.01,
            value=float(initial)
        ).classes('flex-1')

        value_label = ui.label(f'{float(initial):.2f}').classes('w-16 text-right')

        def _on_slider_update(e):
            try:
                new_val = e.args[0] if e.args else slider.value
                value_label.text = f'{float(new_val):.2f}'
            except Exception:
                try:
                    value_label.text = str(slider.value)
                except Exception:
                    value_label.text = ''

        slider.on('update:modelValue', _on_slider_update)
        form_widgets[param_id] = slider
        return slider, value_label


def create_ranged_int_widget(param_id: str, descriptor: Any, initial: int, form_widgets: Dict):
    """Create an integer slider with label showing current integer value."""
    with ui.row().classes('items-center gap-4'):
        slider = ui.slider(
            min=descriptor.range.min,
            max=descriptor.range.max,
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
        return slider, value_label


def create_number_input(param_id: str, initial: Any, format_str: str, form_widgets: Dict):
    """Create a numeric input widget."""
    number_input = ui.number(
        label='',
        value=initial,
        format=format_str
    ).classes('w-full')
    form_widgets[param_id] = number_input
    return number_input


def create_enum_select(param_id: str, options: list, default_label: str, form_widgets: Dict, label_to_key: Dict[str, str] | None = None):
    """Create a select widget and mapping for enum parameters.

    label_to_key: mapping from display label -> canonical key (if provided).
    """
    from frontend.utils.nicegui_compat import select as safe_select
    select = safe_select(
        options,
        label='',
        value=default_label
    ).classes('w-full')  # type: ignore[call-arg]
    if label_to_key is None:
        label_to_key = {opt: opt for opt in options}
    form_widgets[param_id] = {
        'widget': select,
        'label_to_key': label_to_key
    }
    return select


def create_text_input(param_id: str, initial_value: Any, form_widgets: Dict):
    text_input = ui.input(
        label='',
        value=str(initial_value) if initial_value is not None else '',
        placeholder='Enter text...'
    ).classes('w-full')
    form_widgets[param_id] = text_input
    return text_input

