"""Tests for CASE-style JSON-LD fragment builder."""

import json
from pathlib import Path

from case_export.fragment import build_case_fragment_from_job_dict, build_jsonld_text


def test_build_fragment_minimal():
    job = {
        "uid": "abc-123",
        "endpoint": "image_embeddings/search_images",
        "status": "Completed",
        "startTime": "2026-01-01T00:00:00",
        "endTime": "2026-01-01T00:01:00",
        "request": {
            "inputs": {
                "input_dir": {"path": "/tmp/photos"},
                "query": {"text": "sunset"},
            },
            "parameters": {"top_k": 5},
        },
        "response": {
            "root": {
                "output_type": "batchfile",
                "files": [{"path": "/tmp/photos/a.jpg", "file_type": "img", "metadata": {}}],
            }
        },
    }
    doc = build_case_fragment_from_job_dict(job)
    assert "@context" in doc
    assert "@graph" in doc
    assert any("uco:Tool" in str(n.get("@type")) for n in doc["@graph"])
    assert any("uco:Action" in str(n.get("@type")) for n in doc["@graph"])
    s = json.dumps(doc)
    assert "abc-123" in s
    assert "/tmp/photos/a.jpg" in s


def test_build_fragment_serializable():
    job = {"uid": "x", "endpoint": "e", "status": "Completed", "request": {}, "response": None}
    doc = build_case_fragment_from_job_dict(job)
    json.dumps(doc)


def test_posix_path_in_request_serializes():
    """Job dicts from the UI may still have pathlib.Path in input paths."""
    path = Path("/tmp/foo/images")
    job = {
        "uid": "p1",
        "endpoint": "image_summary/summarize-images",
        "status": "Completed",
        "request": {
            "inputs": {
                "input_dir": {"path": path},
                "output_dir": {"path": path},
            },
            "parameters": {},
        },
        "response": None,
    }
    text = build_jsonld_text(job)
    assert "/tmp/foo/images" in text
    json.loads(text)
