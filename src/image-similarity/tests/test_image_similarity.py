"""Tests for image-similarity (/search_series, /export_embeddings, /import_embeddings)."""

import inspect
import json
from pathlib import Path

import pytest
from image_similarity.main import (
    ExportParameters,
    Inputs,
    Parameters,
    _build_metadata,
    _compute_pdq_hash,
    _export_output_filename,
    _export_record_from_row,
    _hit_display_path,
    _import_export_file,
    _import_record_error,
    _is_imported,
    _load_private_embedding_export,
    _write_private_embeddings_export,
    _merge_dedup_key,
    _merge_search_results,
    _parse_export_owner_contact,
    _imported_data_payload,
    export_embeddings,
    export_inputs_cli_parse,
    export_parameters_cli_parse,
    export_task_schema,
    import_inputs_cli_parse,
    import_task_schema,
    inputs_cli_parse,
    parameters_cli_parse,
    search_series,
    task_schema,
)
from rb.api.database import ImageSimilarityPrivateEmbedding
from image_similarity.scorers import (
    CombinedScorer,
    _result_hit_key,
    hamming_distance,
)
from PIL import Image
from rb.api.models import DirectoryInput, FileInput

DEFAULT_MODEL = "google/siglip2-so400m-patch14-384"


def _make_test_image(tmp_path: Path, name: str = "test.png", color: str = "red") -> str:
    path = tmp_path / name
    Image.new("RGB", (64, 64), color=color).save(path)
    return str(path)


def _local_hit(path: str, score: float, content_sha256: str = "abc") -> dict:
    return {
        "path": path,
        "score": score,
        "content_sha256": content_sha256,
        "user_email": "you@x.com",
        "remote": False,
        "source": "local",
    }


def _imported_hit(
    score: float,
    content_sha256: str,
    user_email: str,
    hit_key: str,
    *,
    filename: str = "",
    export_file: str = "",
) -> dict:
    return {
        "path": "[imported]",
        "hit_key": hit_key,
        "score": score,
        "content_sha256": content_sha256,
        "user_email": user_email,
        "remote": True,
        "source": "imported",
        "filename": filename,
        "export_file": export_file,
    }


def _valid_import_record(filename: str = "") -> dict:
    record = {
        "content_sha256": "abc123",
        "embedding": [0.1, 0.2, 0.3],
        "pdq_hash": "a" * 64,
        "user_email": "owner@example.com",
        "privacy_protocol": "clipseg-blackout-v1:person",
        "model_name": DEFAULT_MODEL,
    }
    if filename:
        record["filename"] = filename
    return record


class _FakeScorer:
    def __init__(self, results: list[dict]) -> None:
        self._results = results

    def score(self, query_path: str, candidate_paths: list[str], top_k: int):
        return self._results[:top_k]


# search_series


def test_search_series_task_schema():
    schema = task_schema()
    assert [i.key for i in schema.inputs] == ["input_dir", "query_image"]
    assert [p.key for p in schema.parameters] == [
        "model_name",
        "top_k",
        "min_similarity",
        "scoring_mode",
    ]


def test_search_series_signature():
    assert callable(search_series)
    params = inspect.signature(search_series).parameters
    assert "inputs" in params
    assert "parameters" in params


def test_search_series_inputs_and_parameters(tmp_path: Path):
    folder = tmp_path / "photos"
    folder.mkdir()
    query = tmp_path / "query.jpg"
    query.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)

    inputs = Inputs(
        input_dir=DirectoryInput(path=folder),
        query_image=FileInput(path=query),
    )
    parameters = Parameters(
        model_name=DEFAULT_MODEL,
        top_k=10,
        min_similarity=0.5,
        scoring_mode="combined",
    )

    assert str(inputs["input_dir"].path) == str(folder)
    assert str(inputs["query_image"].path) == str(query)
    assert parameters["top_k"] == 10


def test_search_series_cli_inputs(tmp_path: Path):
    folder = tmp_path / "imgs"
    folder.mkdir()
    query = tmp_path / "q.jpg"
    query.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)

    parsed = inputs_cli_parse(f"{folder}|||{query}")
    assert str(parsed["input_dir"].path) == str(folder)
    assert str(parsed["query_image"].path) == str(query)


def test_search_series_cli_inputs_rejects_wrong_separator():
    with pytest.raises(ValueError, match="Expected"):
        inputs_cli_parse("/some/dir,/some/image.jpg")


def test_search_series_cli_parameters_defaults():
    parsed = parameters_cli_parse("")
    assert parsed["model_name"] == DEFAULT_MODEL
    assert parsed["top_k"] == 5
    assert parsed["min_similarity"] == 0.5
    assert parsed["scoring_mode"] == "combined"


def test_search_series_cli_parameters_full():
    parsed = parameters_cli_parse(f"{DEFAULT_MODEL},7,0.55")
    assert parsed["model_name"] == DEFAULT_MODEL
    assert parsed["top_k"] == 7
    assert parsed["min_similarity"] == 0.55
    assert parsed["scoring_mode"] == "combined"


def test_search_series_cli_scoring_modes():
    assert parameters_cli_parse(f"{DEFAULT_MODEL},5,0.5,pdq")["scoring_mode"] == "pdq"
    assert parameters_cli_parse(",,,semantic")["scoring_mode"] == "semantic"


def test_search_series_cli_rejects_unknown_scoring_mode():
    with pytest.raises(ValueError, match="scoring_mode"):
        parameters_cli_parse(",,,banana")


# combined scoring


def test_combined_scorer_averages_sub_scores():
    clip = _FakeScorer([{"path": "/a.jpg", "score": 0.8}])
    pdq = _FakeScorer([{"path": "/a.jpg", "score": 0.6}])
    scorer = CombinedScorer([("clip", clip, 0.6), ("pdq", pdq, 0.4)])

    hit = scorer.score("q.jpg", ["/a.jpg"], top_k=5)[0]
    assert hit["score"] == 0.72
    assert hit["score_clip"] == 0.8
    assert hit["score_pdq"] == 0.6


def test_combined_scorer_renormalises_when_pdq_missing():
    clip = _FakeScorer([{"path": "/a.jpg", "score": 0.9}])
    pdq = _FakeScorer([])
    scorer = CombinedScorer([("clip", clip, 0.6), ("pdq", pdq, 0.4)])

    assert scorer.score("q.jpg", ["/a.jpg"], top_k=5)[0]["score"] == 0.9


def test_combined_scorer_ranks_by_blended_score():
    clip = _FakeScorer(
        [{"path": "/a.jpg", "score": 0.5}, {"path": "/b.jpg", "score": 0.9}]
    )
    pdq = _FakeScorer(
        [{"path": "/a.jpg", "score": 1.0}, {"path": "/b.jpg", "score": 0.2}]
    )
    scorer = CombinedScorer([("clip", clip, 0.5), ("pdq", pdq, 0.5)])
    ranked = scorer.score("q.jpg", ["/a.jpg", "/b.jpg"], top_k=5)

    assert ranked[0]["path"] == "/a.jpg"
    assert ranked[1]["path"] == "/b.jpg"


def test_combined_scorer_respects_top_k():
    clip = _FakeScorer(
        [
            {"path": "/a.jpg", "score": 0.9},
            {"path": "/b.jpg", "score": 0.8},
            {"path": "/c.jpg", "score": 0.7},
        ]
    )
    pdq = _FakeScorer(
        [
            {"path": "/a.jpg", "score": 0.9},
            {"path": "/b.jpg", "score": 0.8},
            {"path": "/c.jpg", "score": 0.7},
        ]
    )
    scorer = CombinedScorer([("clip", clip, 0.5), ("pdq", pdq, 0.5)])
    assert len(scorer.score("q.jpg", ["/a.jpg", "/b.jpg", "/c.jpg"], top_k=2)) == 2


def test_combined_scorer_keeps_distinct_imported_rows():
    clip = _FakeScorer(
        [
            _imported_hit(0.9, "aaa", "a@x.com", "[imported]#1"),
            _imported_hit(0.7, "bbb", "b@x.com", "[imported]#2"),
        ]
    )
    scorer = CombinedScorer([("clip", clip, 1.0)])
    results = scorer.score("q.jpg", ["/a.jpg"], top_k=5)

    assert len(results) == 2
    assert {r["hit_key"] for r in results} == {"[imported]#1", "[imported]#2"}


def test_combined_scorer_rejects_zero_weights():
    clip = _FakeScorer([])
    with pytest.raises(ValueError, match="weights"):
        CombinedScorer([("clip", clip, 0.0)])


def test_result_hit_key():
    assert _result_hit_key("[imported]", 42) == "[imported]#42"
    assert _result_hit_key("/local/a.jpg", 42) == "/local/a.jpg"


# pdq


def test_pdq_hash_is_64_char_hex(tmp_path: Path):
    digest = _compute_pdq_hash(_make_test_image(tmp_path))
    assert len(digest) == 64
    int(digest, 16)


def test_pdq_hash_is_stable(tmp_path: Path):
    path = _make_test_image(tmp_path)
    assert _compute_pdq_hash(path) == _compute_pdq_hash(path)


def test_pdq_hash_differs_for_different_images(tmp_path: Path):
    red = _make_test_image(tmp_path, "red.png", color="red")
    blue = _make_test_image(tmp_path, "blue.png", color="blue")
    assert _compute_pdq_hash(red) != _compute_pdq_hash(blue)


def test_pdq_hash_bad_file_returns_empty(tmp_path: Path):
    bad = tmp_path / "garbage.png"
    bad.write_bytes(b"not an image")
    assert _compute_pdq_hash(str(bad)) == ""


def test_hamming_distance():
    digest = "a" * 64
    assert hamming_distance(digest, digest) == 0
    assert hamming_distance("0" * 64, "0" * 63 + "1") == 1
    assert hamming_distance("0" * 64, "f" * 64) == 256


# merge plain + private results


def test_merge_search_results_keeps_higher_score():
    private = [_local_hit("/photos/a.jpg", 0.7)]
    plain = [_local_hit("/photos/a.jpg", 0.9)]
    merged = _merge_search_results(private, plain, top_k=5)

    assert len(merged) == 1
    assert merged[0]["score"] == 0.9


def test_merge_search_results_dedupes_imported_by_content_hash():
    private = [_imported_hit(0.8, "abc", "a@x.com", "[imported]#1")]
    plain = [_imported_hit(0.75, "abc", "b@x.com", "[imported]#2")]
    merged = _merge_search_results(private, plain, top_k=5)
    assert len(merged) == 1
    assert merged[0]["score"] == 0.8


def test_merge_search_results_respects_top_k():
    hits = [
        _local_hit(f"/photos/{i}.jpg", score, content_sha256=f"hash{i}")
        for i, score in enumerate([0.9, 0.8, 0.7])
    ]
    merged = _merge_search_results(hits, [], top_k=2)
    assert len(merged) == 2
    assert merged[0]["score"] == 0.9


def test_merge_dedup_key_local():
    hit = {
        "path": "/case/photos/ref_063.jpg",
        "content_sha256": "abc123",
        "user_email": "you@x.com",
        "remote": False,
        "source": "local",
    }
    assert _merge_dedup_key(hit) == ("abc123", "local")


def test_merge_dedup_key_imported():
    full_hash = "a" * 64
    hit = {
        "path": "[imported]",
        "content_sha256": full_hash,
        "user_email": "owner@example.com",
        "remote": True,
        "source": "imported",
    }
    assert _merge_dedup_key(hit) == ("a" * 64, "imported")


# response shaping


def test_hit_display_path():
    full_hash = "a" * 64
    # imported without filename → placeholder
    assert (
        _hit_display_path({"source": "imported", "content_sha256": full_hash})
        == "No filepath provided"
    )
    # imported with filename → filename
    assert (
        _hit_display_path(
            {"source": "imported", "content_sha256": full_hash, "filename": "photo.jpg"}
        )
        == "photo.jpg"
    )
    # imported with empty filename → placeholder
    assert (
        _hit_display_path(
            {"source": "imported", "content_sha256": full_hash, "filename": ""}
        )
        == "No filepath provided"
    )
    # local → basename of path
    assert _hit_display_path({"source": "local", "path": "/photos/a.jpg"}) == "a.jpg"


def test_is_imported():
    assert _is_imported({"source": "imported"}) is True
    assert _is_imported({"source": "local"}) is False
    assert _is_imported({"remote": True}) is True
    assert _is_imported({"remote": False}) is False
    assert _is_imported({}) is False


def test_build_metadata_local_match():
    meta = _build_metadata({"score": 0.8, "bank": "plain", "source": "local"})
    assert meta == {"Source": "Local"}
    assert "Query" not in meta
    assert "Match" not in meta
    assert "Scoring Mode" not in meta
    assert "CLIP Model" not in meta


def test_build_metadata_imported():
    hit = {
        "score": 0.8,
        "bank": "private",
        "source": "imported",
        "content_sha256": "b" * 64,
        "user_email": "owner@example.com",
        "organization": "RescueLab",
        "filename": "photo.jpg",
        "export_file": "export_20250916_120000.json",
    }
    meta = _build_metadata(hit)
    assert "Query" not in meta
    payload = json.loads(meta["Source"])
    assert payload["content_sha256"] == "b" * 64
    assert payload["user_email"] == "owner@example.com"
    assert payload["organization"] == "RescueLab"
    assert payload["imported_from"] == "photo.jpg"
    assert payload["export_file"] == "export_20250916_120000.json"
    assert "source" not in payload
    assert "Embedding type" not in meta
    assert "Content ID" not in meta
    assert "Owner" not in meta


def test_imported_data_payload_full_content_hash():
    payload = _imported_data_payload(
        {"content_sha256": "a" * 64, "source": "imported", "bank": "plain"}
    )
    assert payload["content_sha256"] == "a" * 64
    assert "embedding_type" not in payload
    assert "source" not in payload


# export_embeddings


def test_export_task_schema():
    schema = export_task_schema()
    assert schema.inputs == []
    assert [p.key for p in schema.parameters] == [
        "organization",
        "contact_email",
        "share_filename",
    ]


def test_export_cli():
    assert export_inputs_cli_parse("ignored") == {}
    parsed = export_parameters_cli_parse("RescueLab,team@rescue.example")
    assert parsed["organization"] == "RescueLab"
    assert parsed["contact_email"] == "team@rescue.example"


def test_export_requires_organization():
    with pytest.raises(ValueError, match="organization"):
        _parse_export_owner_contact(
            ExportParameters(organization="", contact_email="a@x.com")
        )


def test_export_requires_contact_email():
    with pytest.raises(ValueError, match="contact_email"):
        _parse_export_owner_contact(
            ExportParameters(organization="RescueLab", contact_email="  ")
        )


def test_export_embeddings_empty_returns_warning(monkeypatch):
    class _FakeResult:
        def all(self):
            return []

    class _FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def exec(self, _stmt):
            return _FakeResult()

    monkeypatch.setattr("image_similarity.main.Session", lambda _engine: _FakeSession())
    result = export_embeddings(
        {},
        ExportParameters(organization="RescueLab", contact_email="team@rescue.example"),
    )
    assert result.root.output_type == "text"
    assert "No local private embeddings found" in result.root.value
    assert "Image Series Similarity" in result.root.value


def test_export_output_filename():
    name = _export_output_filename()
    assert name.startswith("export_")
    assert name.endswith(".json")


def test_import_export_file_prefers_header(tmp_path: Path):
    export_path = tmp_path / "export_20250916_120000.json"
    header = {"export_filename": "export_20250916_120000.json"}
    assert _import_export_file(header, export_path) == export_path.name


def test_import_export_file_falls_back_to_input_path(tmp_path: Path):
    export_path = tmp_path / "received_export.json"
    assert _import_export_file({}, export_path) == "received_export.json"


def test_write_private_embeddings_export_includes_filename(tmp_path: Path):
    output_path = tmp_path / "export_20250916_120000.json"
    _write_private_embeddings_export(output_path, [], "export_20250916_120000.json")
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["export_filename"] == "export_20250916_120000.json"


def test_export_record_uses_stored_filename():
    row = ImageSimilarityPrivateEmbedding(
        path="[imported]",
        content_sha256="abc123",
        embedding=[0.1, 0.2],
        pdq_hash="x" * 64,
        user_email="a@x.com",
        organization="Org",
        privacy_protocol="clipseg-blackout-v1",
        model_name="google/siglip2-so400m-patch14-384",
        filename="photo.jpg",
    )
    record = _export_record_from_row(row)
    assert record["filename"] == "photo.jpg"


def test_export_record_includes_filename_from_path():
    """Export extracts filename from local path."""
    row = ImageSimilarityPrivateEmbedding(
        path="/evidence/case1/photo.jpg",
        content_sha256="abc123",
        embedding=[0.1, 0.2],
        pdq_hash="x" * 64,
        user_email="a@x.com",
        organization="Org",
        privacy_protocol="clipseg-blackout-v1",
        model_name="google/siglip2-so400m-patch14-384",
        filename="",
    )
    record = _export_record_from_row(row)
    assert record["filename"] == "photo.jpg"


def test_export_record_extracts_basename_only():
    """Export strips full path to basename — never leaks directories."""
    row = ImageSimilarityPrivateEmbedding(
        path="/secret/case/evidence/photo.jpg",
        content_sha256="abc123",
        embedding=[0.1, 0.2],
        pdq_hash="x" * 64,
        user_email="a@x.com",
        organization="Org",
        privacy_protocol="clipseg-blackout-v1",
        model_name="google/siglip2-so400m-patch14-384",
        filename="",
    )
    record = _export_record_from_row(row)
    assert record["filename"] == "photo.jpg"


# import_embeddings


def test_import_task_schema():
    schema = import_task_schema()
    assert [i.key for i in schema.inputs] == ["input_file"]
    assert schema.parameters == []


def test_import_cli_inputs(tmp_path: Path):
    export_file = tmp_path / "private_embeddings.json"
    export_file.write_text("{}", encoding="utf-8")
    parsed = import_inputs_cli_parse(str(export_file))
    assert str(parsed["input_file"].path) == str(export_file)


def test_import_record_validation():
    record = _valid_import_record()
    assert _import_record_error(record, 1) is None

    record.pop("pdq_hash")
    assert _import_record_error(record, 1) == "Record 1: missing pdq_hash"

    record = _valid_import_record()
    record["user_email"] = ""
    assert _import_record_error(record, 3) == "Record 3: empty user_email"

    record = _valid_import_record()
    record["embedding"] = []
    assert (
        _import_record_error(record, 2)
        == "Record 2: embedding must be a non-empty list"
    )


def test_load_private_embedding_export(tmp_path: Path):
    export_file = tmp_path / "export.json"
    export_file.write_text(
        '{"format_version": 1, "export_filename": "export.json", "records": [{"content_sha256": "abc"}]}',
        encoding="utf-8",
    )
    header, records = _load_private_embedding_export(export_file)
    assert header == {"format_version": 1, "export_filename": "export.json"}
    assert records == [{"content_sha256": "abc"}]

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid export JSON"):
        _load_private_embedding_export(bad_file)

    empty_file = tmp_path / "empty.json"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Import file is empty"):
        _load_private_embedding_export(empty_file)

    no_records = tmp_path / "no-records.json"
    no_records.write_text('{"format_version": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported export format"):
        _load_private_embedding_export(no_records)

    records_object = tmp_path / "records-object.json"
    records_object.write_text('{"format_version": 1, "records": {}}', encoding="utf-8")
    with pytest.raises(ValueError, match="records must be a list"):
        _load_private_embedding_export(records_object)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
