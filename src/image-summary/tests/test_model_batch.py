"""Tests for batch image description parsing."""

from image_summary.model import (
    parse_batch_descriptions,
    resolve_batch_chunk_size,
    resolve_batch_parallel_workers,
)


def test_parse_batch_descriptions_json_array():
    raw = (
        '[{"file": "a.png", "description": "First"}, '
        '{"file": "b.jpg", "description": "Second"}]'
    )
    paths = ["/data/a.png", "/other/b.jpg"]
    out = parse_batch_descriptions(raw, paths)
    assert out == {"/data/a.png": "First", "/other/b.jpg": "Second"}


def test_parse_batch_descriptions_strips_think():
    raw = "</think>\n" + '[{"file": "x.webp", "description": "ok"}]'
    paths = ["/z/x.webp"]
    assert parse_batch_descriptions(raw, paths) == {"/z/x.webp": "ok"}


def test_parse_batch_descriptions_code_fence():
    raw = '```json\n[{"file": "c.png", "description": "inside"}]\n```'
    paths = ["/c.png"]
    assert parse_batch_descriptions(raw, paths) == {"/c.png": "inside"}


def test_parse_batch_filename_alias_keys():
    raw = '[{"filename": "d.tif", "text": "alias"}]'
    paths = ["/x/d.tif"]
    assert parse_batch_descriptions(raw, paths) == {"/x/d.tif": "alias"}


def test_resolve_batch_chunk_size_explicit():
    assert resolve_batch_chunk_size(50) == 50
    assert resolve_batch_chunk_size(999) == 200  # cap


def test_resolve_batch_chunk_size_env(monkeypatch):
    monkeypatch.setenv("IMAGE_SUMMARY_MAX_IMAGES_PER_BATCH", "12")
    assert resolve_batch_chunk_size(None) == 12
    monkeypatch.delenv("IMAGE_SUMMARY_MAX_IMAGES_PER_BATCH", raising=False)


def test_resolve_batch_chunk_size_default_is_one(monkeypatch):
    """Default is 1 image per Ollama call to avoid cross-image description bleed in batches."""
    monkeypatch.delenv("IMAGE_SUMMARY_MAX_IMAGES_PER_BATCH", raising=False)
    assert resolve_batch_chunk_size(None) == 1


def test_resolve_batch_parallel_workers_explicit():
    assert resolve_batch_parallel_workers(5) == 5
    assert resolve_batch_parallel_workers(99) == 32  # cap


def test_resolve_batch_parallel_workers_env(monkeypatch):
    monkeypatch.setenv("IMAGE_SUMMARY_BATCH_PARALLEL_WORKERS", "3")
    assert resolve_batch_parallel_workers(None) == 3
    monkeypatch.delenv("IMAGE_SUMMARY_BATCH_PARALLEL_WORKERS", raising=False)
