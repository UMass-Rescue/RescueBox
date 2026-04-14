"""Tests for text embeddings search functionality."""

import pytest
from text_embeddings.main import search, task_schema, Inputs, Parameters
from rb.lib.pipeline_corpus import resolve_text_file_corpus_paths
from rb.api.models import TextInput, DirectoryInput, BatchFileInput, FileInput
from pathlib import Path


def test_search_task_schema():
    """Test that search task schema is properly defined."""
    schema = task_schema()
    assert schema is not None
    assert len(schema.inputs) == 2
    assert schema.inputs[0].key == "input_dir"
    assert schema.inputs[1].key == "query"
    assert len(schema.parameters) == 2
    assert schema.parameters[0].key == "top_k"
    assert schema.parameters[1].key == "min_similarity"


def test_search_corpus_paths_file_filter_does_not_scan_siblings(tmp_path: Path):
    """Pipeline file_filter limits corpus; stale .txt in the same dir are ignored."""
    stale = tmp_path / "stale.txt"
    keep = tmp_path / "keep.txt"
    stale.write_text("old", encoding="utf-8")
    keep.write_text("new", encoding="utf-8")
    inputs = {
        "input_dir": DirectoryInput(path=tmp_path),
        "query": TextInput(text="q"),
        "file_filter": BatchFileInput(files=[FileInput(path=keep)]),
    }
    paths, err = resolve_text_file_corpus_paths(inputs, str(tmp_path))
    assert err == ""
    assert paths == [str(keep)]


def test_search_corpus_paths_empty_file_filter_no_fallback(tmp_path: Path):
    """Explicit empty file_filter must not fall back to directory listing."""
    (tmp_path / "only.txt").write_text("x", encoding="utf-8")
    inputs = {
        "input_dir": DirectoryInput(path=tmp_path),
        "query": TextInput(text="q"),
        "file_filter": BatchFileInput(files=[]),
    }
    paths, err = resolve_text_file_corpus_paths(inputs, str(tmp_path))
    assert paths == []
    assert "empty" in err.lower()


def test_search_corpus_paths_dict_file_filter_matches_pipeline_payload(tmp_path: Path):
    """Merged JSON may expose file_filter as plain dicts (e.g. from chained jobs)."""
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("1", encoding="utf-8")
    b.write_text("2", encoding="utf-8")
    inputs = {
        "input_dir": DirectoryInput(path=tmp_path),
        "query": TextInput(text="q"),
        "file_filter": {
            "files": [{"path": str(a)}, {"path": str(b)}],
        },
    }
    paths, err = resolve_text_file_corpus_paths(inputs, str(tmp_path))
    assert err == ""
    assert paths == [str(a), str(b)]


def test_search_types():
    """Test search input/output types."""
    assert callable(search)

    import inspect
    sig = inspect.signature(search)
    assert "inputs" in sig.parameters
    assert "parameters" in sig.parameters


def test_search_inputs_structure():
    """Test that Inputs has correct structure."""
    inputs = Inputs(
        input_dir=DirectoryInput(path=Path("/tmp")),
        query=TextInput(text="test query"),
    )
    assert "input_dir" in inputs
    assert "query" in inputs
    assert inputs["query"].text == "test query"


def test_search_parameters_structure():
    """Test that Parameters has correct structure."""
    params = Parameters(top_k=5)
    assert params["top_k"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
