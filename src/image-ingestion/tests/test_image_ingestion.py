from unittest.mock import MagicMock, patch

from image_ingestion import hashers
from image_ingestion.main import (
    _ingest,
    _selected_hashes,
    delete_archive,
    delete_parameters_cli_parse,
    delete_task_schema,
    ingest_images,
    ingest_parameters_cli_parse,
    ingest_task_schema,
    rename_archive,
    rename_task_schema,
)
from rb.api.database import FileRecord
from rb.api.models import DirectoryInput

ALL_YES = {"md5": "yes", "pdq": "yes", "semantic": "yes", "essay": "yes"}


def test_ingest_schema_has_label_description_and_four_hash_options():
    schema = ingest_task_schema()
    assert [i.key for i in schema.inputs] == ["input_dir"]
    assert [p.key for p in schema.parameters] == [
        "label",
        "description",
        "md5",
        "pdq",
        "semantic",
        "essay",
    ]


def test_delete_and_rename_schemas():
    assert [p.key for p in delete_task_schema().parameters] == [
        "label",
        "retain_hashes",
    ]
    assert [p.key for p in rename_task_schema().parameters] == [
        "old_label",
        "new_label",
    ]


def test_semantic_option_also_selects_private_hash():
    selected = _selected_hashes({**ALL_YES, "essay": "no", "md5": "no"})
    assert selected == ["pdq", "semantic", "private"]


def test_fill_missing_computes_only_missing_hashes():
    record = FileRecord(sha256="a" * 64, md5="existing")
    fake_hashers = {"md5": MagicMock(), "pdq": MagicMock(return_value="pdq-value")}
    with patch.dict(hashers.HASHERS, fake_hashers):
        computed = hashers.fill_missing(record, "img.jpg", ["md5", "pdq"])
    assert computed == 1
    assert record.pdq_hash == "pdq-value"
    fake_hashers["md5"].assert_not_called()


def test_ingest_stores_duplicate_content_once_but_links_both_paths():
    store = MagicMock()
    with (
        patch("image_ingestion.main.archive_store", store),
        patch("image_ingestion.main.sha256_file", return_value="h" * 64),
        patch("image_ingestion.main.fill_missing", return_value=1),
    ):
        _ingest(MagicMock(), "case", "", ["a.jpg", "b.jpg"], ["md5"])
    store.find_or_create_file.assert_called_once()
    linked = store.link_files.call_args.args[2]
    assert linked == {"a.jpg": "h" * 64, "b.jpg": "h" * 64}


def test_delete_and_rename_report_missing_label():
    store = MagicMock()
    store.find_archive.return_value = None
    with (
        patch("image_ingestion.main.archive_store", store),
        patch("image_ingestion.main.Session"),
    ):
        deleted = delete_archive({}, {"label": "nope", "retain_hashes": "yes"})
        renamed = rename_archive({}, {"old_label": "nope", "new_label": "new"})
    assert deleted.root.title == "Archive not found"
    assert renamed.root.title == "Archive not found"
    store.delete_archive.assert_not_called()
    store.rename_archive.assert_not_called()


def test_ingest_rejects_existing_label(tmp_path):
    store = MagicMock()
    with (
        patch("image_ingestion.main.archive_store", store),
        patch("image_ingestion.main.Session"),
    ):
        result = ingest_images(
            {"input_dir": DirectoryInput(path=str(tmp_path))},
            {"label": "case", "description": "", **ALL_YES},
        )
    assert result.root.title == "Label already in use"
    store.create_archive.assert_not_called()


def test_rename_rejects_existing_new_label():
    store = MagicMock()
    with (
        patch("image_ingestion.main.archive_store", store),
        patch("image_ingestion.main.Session"),
    ):
        result = rename_archive({}, {"old_label": "a", "new_label": "b"})
    assert result.root.title == "Label already in use"
    store.rename_archive.assert_not_called()


def test_cli_parsers():
    params = ingest_parameters_cli_parse("case|details|yes|no|yes|no")
    assert params["label"] == "case"
    assert params["pdq"] == "no"
    assert delete_parameters_cli_parse("case,no") == {
        "label": "case",
        "retain_hashes": "no",
    }
