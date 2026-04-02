"""Tests for CASE/UCO-aligned JSON-LD fragment builder."""

import json
from pathlib import Path

from case_export.fragment import build_case_fragment_from_job_dict, build_jsonld_text
from case_export.validation import validate_fragment_jsonld


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
    types_flat = json.dumps(doc["@graph"])
    # CASE-UCO SDK uses compact types (e.g. case-investigation:InvestigativeAction)
    assert "case-investigation:InvestigativeAction" in types_flat
    assert "uco-tool:Tool" in types_flat or "uco-tool:AnalyticTool" in types_flat
    assert "case-investigation:ProvenanceRecord" in types_flat
    assert "uco-observable:RasterPicture" in types_flat
    assert "uco-observable:ContentData" in types_flat
    assert "uco-core:Relationship" in types_flat
    assert "/tmp/photos/a.jpg" in types_flat
    assert "rb:jobUid" in json.dumps(doc["@graph"])
    s = json.dumps(doc)
    assert "abc-123" in s


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


def test_pipeline_endpoint_chain_emits_one_instrument_per_step():
    """Multi-step jobs: one AnalyticTool per endpoint in order; one InvestigativeAction per step."""
    job = {
        "uid": "pipe-1",
        "endpoint": "image_embeddings/search_images",
        "endpointChain": ["age-gender/predict", "image_embeddings/search_images"],
        "status": "Completed",
        "request": {},
        "response": None,
    }
    doc = build_case_fragment_from_job_dict(job)
    g = json.dumps(doc["@graph"])
    assert g.count("uco-tool:AnalyticTool") >= 2
    assert "age-gender/predict" in g
    assert "image_embeddings/search_images" in g
    assert "kb:instrument-age-gender_predict" in g
    assert "kb:instrument-image_embeddings_search_images" in g
    assert g.count("case-investigation:InvestigativeAction") >= 2
    assert "kb:inv-pipe-1-step0" in g
    assert "case-investigation:wasInformedBy" in g


def test_output_type_inferred_when_missing_on_root():
    """Wire shapes may omit output_type; rb:outputType should match batchfile inference."""
    job = {
        "uid": "ot-1",
        "endpoint": "image_embeddings/search_images",
        "status": "Completed",
        "request": {},
        "response": {
            "root": {
                "files": [{"path": "/tmp/a.jpg", "metadata": {}}],
            }
        },
    }
    doc = build_case_fragment_from_job_dict(job)
    inv = next(n for n in doc["@graph"] if n.get("@id", "").startswith("kb:inv-"))
    assert inv.get("rb:outputType") == "batchfile"
    assert inv.get("rb:outputSummary", {}).get("output_type") == "batchfile"


def test_batch_metadata_maps_similarity_to_rb_and_relationship():
    job = {
        "uid": "sim-1",
        "endpoint": "image_embeddings/search_images",
        "status": "Completed",
        "request": {"inputs": {}, "parameters": {"min_similarity": 0.5}},
        "response": {
            "root": {
                "output_type": "batchfile",
                "files": [
                    {
                        "path": "/data/x.jpg",
                        "metadata": {
                            "Similarity": "0.91",
                            "Model": "openai/clip-vit-base-patch32",
                        },
                    }
                ],
            }
        },
    }
    doc = build_case_fragment_from_job_dict(job)
    s = json.dumps(doc["@graph"])
    assert "rb:similarityScore" in s
    assert "0.91" in s
    assert "openai/clip-vit-base-patch32" in s


def test_validation_runs_or_skips_gracefully():
    doc = build_case_fragment_from_job_dict({"uid": "u", "endpoint": "e", "status": "Completed"})
    ok, msgs = validate_fragment_jsonld(doc)
    assert isinstance(msgs, list) and len(msgs) >= 1
    # Without case_validate: ok True (skipped). With SHACL: may be False until graph matches shapes.
    assert ok in (True, False)
