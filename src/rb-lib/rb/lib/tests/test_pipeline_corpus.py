"""Unit tests for pipeline corpus resolution (file_filter vs directory scan)."""

from __future__ import annotations

from rb.api.models import BatchFileInput, FileInput
from rb.lib.pipeline_corpus import (
    get_file_filter_from_inputs,
    list_text_files_in_directory,
    resolve_text_file_corpus_paths,
)


class _Obj:
    """Minimal object with optional file_filter for get_file_filter_from_inputs."""

    def __init__(self, file_filter=None):
        self.file_filter = file_filter


def test_list_text_files_in_directory_sorted_and_non_recursive(tmp_path):
    sub = tmp_path / "nested"
    sub.mkdir()
    (sub / "inner.txt").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "skip.bin").write_bytes(b"\x00")
    paths = list_text_files_in_directory(str(tmp_path))
    assert paths == [str(tmp_path / "a.txt"), str(tmp_path / "b.txt")]


def test_list_text_files_in_directory_empty_on_missing_dir(tmp_path):
    missing = tmp_path / "nope"
    assert list_text_files_in_directory(str(missing)) == []


def test_list_text_files_in_directory_respects_extensions(tmp_path):
    (tmp_path / "a.md").write_text("m", encoding="utf-8")
    (tmp_path / "b.txt").write_text("t", encoding="utf-8")
    only_md = list_text_files_in_directory(str(tmp_path), allowed_extensions=frozenset({".md"}))
    assert only_md == [str(tmp_path / "a.md")]


def test_get_file_filter_from_inputs_dict_and_object():
    ff = BatchFileInput(files=[])
    assert get_file_filter_from_inputs({"file_filter": ff}) is ff
    assert get_file_filter_from_inputs({"other": 1}) is None
    assert get_file_filter_from_inputs(_Obj(ff)) is ff
    assert get_file_filter_from_inputs(_Obj(None)) is None


def test_resolve_no_filter_scans_directory(tmp_path):
    (tmp_path / "one.txt").write_text("a", encoding="utf-8")
    paths, err = resolve_text_file_corpus_paths({}, str(tmp_path))
    assert err == ""
    assert paths == [str(tmp_path / "one.txt")]


def test_resolve_no_filter_empty_directory(tmp_path):
    paths, err = resolve_text_file_corpus_paths({}, str(tmp_path))
    assert paths == []
    assert "No text files" in err


def test_resolve_custom_empty_dir_error(tmp_path):
    paths, err = resolve_text_file_corpus_paths(
        {}, str(tmp_path), empty_dir_error="custom empty"
    )
    assert paths == []
    assert err == "custom empty"


def test_resolve_file_filter_dict_style_paths(tmp_path):
    """HTTP-merged dict may use dict file_filter with path strings (no Pydantic models)."""
    keep = tmp_path / "keep.txt"
    keep.write_text("ok", encoding="utf-8")
    inputs = {
        "file_filter": {"files": [{"path": str(keep)}]},
    }
    (tmp_path / "ignored.txt").write_text("no", encoding="utf-8")
    paths, err = resolve_text_file_corpus_paths(inputs, str(tmp_path))
    assert err == ""
    assert paths == [str(keep)]


def test_resolve_file_filter_skips_missing_paths(tmp_path):
    """Paths in file_filter that are not files are skipped; Pydantic FileInput requires existing files."""
    missing = str(tmp_path / "gone.txt")
    inputs = {
        "file_filter": {"files": [{"path": missing}]},
    }
    (tmp_path / "present.txt").write_text("x", encoding="utf-8")
    paths, err = resolve_text_file_corpus_paths(inputs, str(tmp_path))
    assert paths == []
    assert "exist on disk" in err.lower()


def test_resolve_file_filter_skips_entries_without_path(tmp_path):
    (tmp_path / "only.txt").write_text("x", encoding="utf-8")
    inputs = {
        "file_filter": {"files": [{}, {"path": str(tmp_path / "only.txt")}]},
    }
    paths, err = resolve_text_file_corpus_paths(inputs, str(tmp_path))
    assert err == ""
    assert paths == [str(tmp_path / "only.txt")]


def test_resolve_file_filter_path_object(tmp_path):
    p = tmp_path / "p.txt"
    p.write_text("z", encoding="utf-8")
    inputs = {"file_filter": BatchFileInput(files=[FileInput(path=p)])}
    paths, err = resolve_text_file_corpus_paths(inputs, str(tmp_path))
    assert err == ""
    assert paths == [str(p)]
