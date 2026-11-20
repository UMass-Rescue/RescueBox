from unittest.mock import patch

from frontend.utils.image_archive_validation import (
    DELETE_ENDPOINT,
    INGEST_ENDPOINT,
    RENAME_ENDPOINT,
    use_archive_label_picker,
    validate_image_archive_form,
)

FETCH = "frontend.utils.image_archive_validation.fetch_archive_labels"


def _ingest_form(path: str, label: str) -> dict:
    return {"inputs": {"input_dir": {"path": path}}, "parameters": {"label": label}}


@patch(FETCH, return_value=["taken"])
def test_ingest_rejects_duplicate_label(_fetch):
    errors = validate_image_archive_form(
        _ingest_form("/data/case-a", "taken"), INGEST_ENDPOINT
    )
    assert errors == {"label": "An archive with the label 'taken' already exists."}


@patch(FETCH, return_value=["series_0013"])
def test_ingest_default_label_from_folder_name(_fetch):
    errors = validate_image_archive_form(
        _ingest_form("/data/series_0013", ""), INGEST_ENDPOINT
    )
    assert "series_0013" in errors["label"]


@patch(FETCH, return_value=["other"])
def test_ingest_allows_new_label(_fetch):
    form = _ingest_form("/data/new-case", "fresh")
    assert validate_image_archive_form(form, INGEST_ENDPOINT) == {}


def test_delete_requires_selection():
    errors = validate_image_archive_form({"parameters": {"label": ""}}, DELETE_ENDPOINT)
    assert errors == {"label": "Choose an archive from the list."}


@patch(FETCH, return_value=["a", "b"])
def test_rename_rejects_taken_new_label(_fetch):
    form = {"parameters": {"old_label": "a", "new_label": "b"}}
    errors = validate_image_archive_form(form, RENAME_ENDPOINT)
    assert errors == {"new_label": "An archive with the label 'b' already exists."}


@patch(FETCH, return_value=["a"])
def test_rename_requires_new_label(_fetch):
    form = {"parameters": {"old_label": "a", "new_label": "  "}}
    errors = validate_image_archive_form(form, RENAME_ENDPOINT)
    assert errors == {"new_label": "Enter a new investigation label."}


@patch(FETCH)
def test_other_endpoints_skip_backend_call(fetch):
    assert validate_image_archive_form({}, "audio/transcribe") == {}
    fetch.assert_not_called()


def test_picker_only_for_existing_archive_fields():
    assert use_archive_label_picker(DELETE_ENDPOINT, "label")
    assert use_archive_label_picker(RENAME_ENDPOINT, "old_label")
    assert not use_archive_label_picker(RENAME_ENDPOINT, "new_label")
    assert not use_archive_label_picker(INGEST_ENDPOINT, "label")
