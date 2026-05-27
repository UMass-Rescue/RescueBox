"""Unit tests for job form input/output path helpers."""

from pathlib import Path
from unittest.mock import MagicMock

from rb.api.models import InputSchema, InputType


def test_suggested_outputs_dir_path():
    from frontend.utils import suggested_outputs_dir_path

    s = suggested_outputs_dir_path("/home/user/project/case/images")
    assert "case" in s
    assert isinstance(s, str)


def test_paired_output_directory_field_id():
    from frontend.utils import paired_output_directory_field_id

    inputs = [
        InputSchema(
            key="input_dir",
            label="in",
            input_type=InputType.DIRECTORY,
        ),
        InputSchema(
            key="output_dir",
            label="out",
            input_type=InputType.DIRECTORY,
        ),
    ]
    assert paired_output_directory_field_id(inputs, 0) == "output_dir"
    assert paired_output_directory_field_id(inputs, 1) is None

    deepfake = [
        InputSchema(
            key="input_dataset",
            label="in",
            input_type=InputType.DIRECTORY,
        ),
        InputSchema(
            key="output_file",
            label="out",
            input_type=InputType.DIRECTORY,
        ),
    ]
    assert paired_output_directory_field_id(deepfake, 0) == "output_file"


def test_maybe_autofill_output_dir_field_skips_when_nonempty():
    from frontend.utils import maybe_autofill_output_dir_field

    out = MagicMock()
    out.value = "/already/set"
    form_widgets = {"output_dir": out}
    maybe_autofill_output_dir_field(form_widgets, "output_dir", "/tmp/in")
    out.set_value.assert_not_called()


def test_maybe_autofill_output_dir_field_sets_when_empty():
    from frontend.utils import maybe_autofill_output_dir_field

    out = MagicMock()
    out.value = ""
    out.set_value = MagicMock()
    form_widgets = {"output_dir": out}
    maybe_autofill_output_dir_field(form_widgets, "output_dir", "/tmp/case/images")
    out.set_value.assert_called_once()
    called = out.set_value.call_args[0][0]
    assert "case" in called


def test_suggested_ufdr_mount_folder_path():
    from frontend.utils import suggested_ufdr_mount_folder_path

    s = suggested_ufdr_mount_folder_path(
        "/home/tester/Documents/demo5/ufdr-mount/inputs/test.ufdr"
    )
    assert s == str(
        Path("/home/tester/Documents/demo5/ufdr-mount/outputs").resolve()
    )


def test_paired_ufdr_mount_name_field_id():
    from frontend.utils import paired_ufdr_mount_name_field_id

    ufdr_schema = [
        InputSchema(
            key="ufdr_file",
            label="UFDR",
            input_type=InputType.FILE,
        ),
        InputSchema(
            key="mount_name",
            label="Mount",
            input_type=InputType.TEXT,
        ),
    ]
    assert paired_ufdr_mount_name_field_id(ufdr_schema, 0) == "mount_name"
    assert paired_ufdr_mount_name_field_id(ufdr_schema, 1) is None
