from unittest.mock import MagicMock, patch

from image_ingestion import hashers
from image_ingestion.main import (
    _ingest,
    _selected_hashes,
    delete_parameters_cli_parse,
    delete_task_schema,
    ingest_parameters_cli_parse,
    ingest_task_schema,
    rename_task_schema,
)
from rb.api.database import FileRecord

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
        computed = _ingest(MagicMock(), "case", "", ["a.jpg", "b.jpg"], ["md5"])
    assert computed == 1
    store.find_or_create_file.assert_called_once()
    linked = store.link_files.call_args.args[2]
    assert linked == {"a.jpg": "h" * 64, "b.jpg": "h" * 64}


def test_cli_parsers():
    params = ingest_parameters_cli_parse("case|details|yes|no|yes|no")
    assert params["label"] == "case"
    assert params["pdq"] == "no"
    assert delete_parameters_cli_parse("case,no") == {
        "label": "case",
        "retain_hashes": "no",
    }
