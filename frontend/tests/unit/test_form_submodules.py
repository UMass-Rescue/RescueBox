"""Unit tests for extracted form input submodules."""

from unittest.mock import MagicMock, patch

import pytest
from nicegui import ui

from frontend.components.forms.parameter_fields import (
    _get_ranged_float_values,
    _get_ranged_int_values,
    _is_ranged_float_descriptor,
    _is_ranged_int_descriptor,
    create_parameter_field,
)
from frontend.components.forms.path_inputs import (
    create_directory_input,
    create_file_input,
)


def test_ranged_float_helpers():
    desc_dict = {"parameter_type": "ranged_float", "range": {"min": 0.1, "max": 0.9}, "default": 0.5}
    assert _is_ranged_float_descriptor(desc_dict) is True
    rmin, rmax, rdef = _get_ranged_float_values(desc_dict)
    assert rmin == 0.1
    assert rmax == 0.9
    assert rdef == 0.5


def test_ranged_int_helpers():
    desc_dict = {"parameterType": "ranged_int", "range": {"min": 1, "max": 10}, "default": 5}
    assert _is_ranged_int_descriptor(desc_dict) is True
    rmin, rmax, rdef = _get_ranged_int_values(desc_dict)
    assert rmin == 1
    assert rmax == 10
    assert rdef == 5


@pytest.mark.asyncio
async def test_create_parameter_field_numeric():
    form_widgets = {}
    param_schema = {
        "key": "confidence",
        "label": "Confidence",
        "value": {
            "parameter_type": "ranged_float",
            "range": {"min": 0.0, "max": 1.0},
            "default": 0.7,
        },
    }
    with patch.object(ui, "column"), patch.object(ui, "label"), patch.object(ui, "number") as mock_number:
        mock_number.return_value.classes.return_value = "widget"
        await create_parameter_field(param_schema, form_widgets, {"confidence": 0.8})
        assert "confidence" in form_widgets


def test_create_directory_input():
    form_widgets = {}
    with patch.object(ui, "column"), patch.object(ui, "row"), patch.object(
        ui, "label"
    ), patch.object(ui, "input") as mock_input, patch.object(ui, "icon"), patch.object(ui, "button"):
        mock_input.return_value.classes.return_value.props.return_value = mock_input.return_value
        create_directory_input("input_dir", {"path": "/tmp/test"}, form_widgets)
        assert "input_dir" in form_widgets


def test_create_file_input():
    form_widgets = {}
    with patch.object(ui, "column"), patch.object(ui, "row"), patch.object(
        ui, "label"
    ), patch.object(ui, "input") as mock_input, patch.object(ui, "icon"), patch.object(ui, "button"):
        mock_input.return_value.classes.return_value.props.return_value = mock_input.return_value
        create_file_input("input_file", "/tmp/test.jpg", form_widgets)
        assert "input_file" in form_widgets
