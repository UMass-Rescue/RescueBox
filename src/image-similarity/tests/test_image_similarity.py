"""Tests for image similarity plugin (image-to-image CLIP search)."""

import inspect

import pytest
from image_similarity.main import (
    search_similar_images,
    task_schema,
    Inputs,
    Parameters,
    inputs_cli_parse,
    parameters_cli_parse,
    _compute_pdq_hash,
)
from image_similarity.scorers import (
    hamming_distance,
    CombinedScorer,
)
from rb.api.models import DirectoryInput, FileInput
from PIL import Image


# ---------------------------------------------------------------------------
#  Task schema
# ---------------------------------------------------------------------------

def test_task_schema_inputs():
    schema = task_schema()
    assert schema is not None
    assert len(schema.inputs) == 2
    assert schema.inputs[0].key == "input_dir"
    assert schema.inputs[1].key == "query_image"


def test_task_schema_parameters():
    schema = task_schema()
    assert len(schema.parameters) == 4
    keys = [p.key for p in schema.parameters]
    assert keys == ["model_name", "top_k", "min_similarity", "scoring_mode"]


# ---------------------------------------------------------------------------
#  Function signature
# ---------------------------------------------------------------------------

def test_search_similar_images_callable():
    assert callable(search_similar_images)
    sig = inspect.signature(search_similar_images)
    assert "inputs" in sig.parameters
    assert "parameters" in sig.parameters


# ---------------------------------------------------------------------------
#  Input / parameter types
# ---------------------------------------------------------------------------

def test_inputs_structure(tmp_path):
    d = tmp_path / "photos"
    d.mkdir()
    img = tmp_path / "query.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
    inputs = Inputs(
        input_dir=DirectoryInput(path=d),
        query_image=FileInput(path=img),
    )
    assert str(inputs["query_image"].path) == str(img)
    assert str(inputs["input_dir"].path) == str(d)


def test_parameters_structure():
    params = Parameters(
        model_name="openai/clip-vit-base-patch32",
        top_k=10,
        min_similarity=0.5,
        scoring_mode="combined",
    )
    assert params["top_k"] == 10
    assert params["min_similarity"] == 0.5
    assert params["model_name"] == "openai/clip-vit-base-patch32"
    assert params["scoring_mode"] == "combined"


# ---------------------------------------------------------------------------
#  CLI parsers
# ---------------------------------------------------------------------------

def test_inputs_cli_parse(tmp_path):
    d = tmp_path / "imgs"
    d.mkdir()
    img = tmp_path / "q.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
    parsed = inputs_cli_parse(f"{d}|||{img}")
    assert str(parsed["input_dir"].path) == str(d)
    assert str(parsed["query_image"].path) == str(img)


def test_inputs_cli_parse_missing_separator():
    with pytest.raises(ValueError, match="Expected"):
        inputs_cli_parse("/some/dir,/some/image.jpg")


def test_parameters_cli_parse_full():
    parsed = parameters_cli_parse("openai/clip-vit-base-patch32,7,0.55")
    assert parsed["model_name"] == "openai/clip-vit-base-patch32"
    assert parsed["top_k"] == 7
    assert parsed["min_similarity"] == 0.55
    assert parsed["scoring_mode"] == "combined"


def test_parameters_cli_parse_defaults():
    parsed = parameters_cli_parse("")
    assert parsed["model_name"] == "google/siglip2-so400m-patch14-384"
    assert parsed["top_k"] == 5
    assert parsed["min_similarity"] == 0.5
    assert parsed["scoring_mode"] == "combined"


def test_parameters_cli_parse_with_scoring_mode():
    parsed = parameters_cli_parse("openai/clip-vit-base-patch32,5,0.5,pdq")
    assert parsed["scoring_mode"] == "pdq"

    parsed = parameters_cli_parse(",,,semantic")
    assert parsed["scoring_mode"] == "semantic"


def test_parameters_cli_parse_invalid_scoring_mode():
    with pytest.raises(ValueError, match="scoring_mode"):
        parameters_cli_parse(",,,banana")


# ---------------------------------------------------------------------------
#  Hamming distance (pure math, no deps)
# ---------------------------------------------------------------------------

def test_hamming_distance_identical():
    h = "a" * 64
    assert hamming_distance(h, h) == 0


def test_hamming_distance_one_bit():
    a = "0" * 64
    b = "0" * 63 + "1"
    assert hamming_distance(a, b) == 1


def test_hamming_distance_all_different():
    a = "0" * 64
    b = "f" * 64
    assert hamming_distance(a, b) == 256


def test_hamming_distance_symmetric():
    a = "abcdef0123456789" * 4
    b = "1234567890abcdef" * 4
    assert hamming_distance(a, b) == hamming_distance(b, a)


# ---------------------------------------------------------------------------
#  PDQ hash computation (needs only PIL, no DB)
# ---------------------------------------------------------------------------

def _make_test_image(tmp_path, name="test.png", size=(64, 64), color="red"):
    """Create a small solid-color image and return its path."""
    img = Image.new("RGB", size, color=color)
    p = tmp_path / name
    img.save(str(p))
    return str(p)


def test_compute_pdq_hash_returns_hex(tmp_path):
    path = _make_test_image(tmp_path)
    h = _compute_pdq_hash(path)
    assert len(h) == 64
    int(h, 16)  # must be valid hex


def test_compute_pdq_hash_deterministic(tmp_path):
    path = _make_test_image(tmp_path)
    assert _compute_pdq_hash(path) == _compute_pdq_hash(path)


def test_compute_pdq_hash_different_images(tmp_path):
    red = _make_test_image(tmp_path, "red.png", color="red")
    blue = _make_test_image(tmp_path, "blue.png", color="blue")
    assert _compute_pdq_hash(red) != _compute_pdq_hash(blue)


def test_compute_pdq_hash_bad_file(tmp_path):
    bad = tmp_path / "garbage.png"
    bad.write_bytes(b"not an image")
    assert _compute_pdq_hash(str(bad)) == ""


# ---------------------------------------------------------------------------
#  CombinedScorer (mock sub-scorers, no DB)
# ---------------------------------------------------------------------------

class _FakeScorer:
    """Minimal scorer that returns pre-set results."""

    def __init__(self, results: list[dict]):
        self._results = results

    def score(self, query_path, candidate_paths, top_k):
        return self._results[:top_k]


def test_combined_scorer_equal_weights():
    clip = _FakeScorer([{"path": "/a.jpg", "score": 0.8}])
    pdq = _FakeScorer([{"path": "/a.jpg", "score": 0.6}])
    scorer = CombinedScorer([("clip", clip, 0.5), ("pdq", pdq, 0.5)])
    results = scorer.score("q.jpg", ["/a.jpg"], top_k=5)
    assert len(results) == 1
    assert results[0]["score"] == 0.7
    assert results[0]["score_clip"] == 0.8
    assert results[0]["score_pdq"] == 0.6


def test_combined_scorer_unequal_weights():
    clip = _FakeScorer([{"path": "/a.jpg", "score": 1.0}])
    pdq = _FakeScorer([{"path": "/a.jpg", "score": 0.0}])
    scorer = CombinedScorer([("clip", clip, 3.0), ("pdq", pdq, 1.0)])
    results = scorer.score("q.jpg", ["/a.jpg"], top_k=5)
    assert results[0]["score"] == 0.75


def test_combined_scorer_renormalises_missing_scorer():
    """If a path only appears in one scorer's results, it should NOT be penalised."""
    clip = _FakeScorer([{"path": "/a.jpg", "score": 0.9}])
    pdq = _FakeScorer([])  # no PDQ results
    scorer = CombinedScorer([("clip", clip, 0.5), ("pdq", pdq, 0.5)])
    results = scorer.score("q.jpg", ["/a.jpg"], top_k=5)
    assert len(results) == 1
    assert results[0]["score"] == 0.9


def test_combined_scorer_ranking():
    clip = _FakeScorer([
        {"path": "/a.jpg", "score": 0.5},
        {"path": "/b.jpg", "score": 0.9},
    ])
    pdq = _FakeScorer([
        {"path": "/a.jpg", "score": 1.0},
        {"path": "/b.jpg", "score": 0.2},
    ])
    scorer = CombinedScorer([("clip", clip, 0.5), ("pdq", pdq, 0.5)])
    results = scorer.score("q.jpg", ["/a.jpg", "/b.jpg"], top_k=5)
    assert results[0]["path"] == "/a.jpg"  # (0.5+1.0)/2 = 0.75
    assert results[1]["path"] == "/b.jpg"  # (0.9+0.2)/2 = 0.55


def test_combined_scorer_top_k():
    clip = _FakeScorer([
        {"path": "/a.jpg", "score": 0.9},
        {"path": "/b.jpg", "score": 0.8},
        {"path": "/c.jpg", "score": 0.7},
    ])
    pdq = _FakeScorer([
        {"path": "/a.jpg", "score": 0.9},
        {"path": "/b.jpg", "score": 0.8},
        {"path": "/c.jpg", "score": 0.7},
    ])
    scorer = CombinedScorer([("clip", clip, 0.5), ("pdq", pdq, 0.5)])
    results = scorer.score("q.jpg", ["/a.jpg", "/b.jpg", "/c.jpg"], top_k=2)
    assert len(results) == 2


def test_combined_scorer_zero_weights_raises():
    clip = _FakeScorer([])
    with pytest.raises(ValueError, match="weights"):
        CombinedScorer([("clip", clip, 0.0)])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
