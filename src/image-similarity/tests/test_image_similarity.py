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
)
from rb.api.models import DirectoryInput, FileInput


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
    assert len(schema.parameters) == 2
    keys = [p.key for p in schema.parameters]
    assert keys == ["top_k", "min_similarity"]


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
        top_k=10,
        min_similarity=0.5,
    )
    assert params["top_k"] == 10
    assert params["min_similarity"] == 0.5


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
    parsed = parameters_cli_parse("7,0.55")
    assert parsed["top_k"] == 7
    assert parsed["min_similarity"] == 0.55


def test_parameters_cli_parse_defaults():
    parsed = parameters_cli_parse("")
    assert parsed["top_k"] == 5
    assert parsed["min_similarity"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
