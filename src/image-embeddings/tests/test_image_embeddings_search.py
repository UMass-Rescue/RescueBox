"""Tests for image embeddings embed+search (single endpoint)."""

import pytest
from image_embeddings.main import (
    DEFAULT_CLIP_MODEL,
    ClipImageDirectory,
    task_schema,
    Inputs,
    Parameters,
)
from rb.api.models import TextInput


def test_task_schema():
    """Test combined task schema."""
    schema = task_schema()
    assert schema is not None
    keys = [i.key for i in schema.inputs]
    assert keys == ["input_dir", "query"]


def test_inputs_structure(tmp_path):
    d = tmp_path / "photos"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"\xff\xd8\xff")
    inputs = Inputs(
        input_dir=ClipImageDirectory(path=d),
        query=TextInput(text="sunset over ocean"),
    )
    assert isinstance(inputs["query"], TextInput)
    assert inputs["query"].text == "sunset over ocean"


def test_parameters_structure():
    params = Parameters(
        model_name=DEFAULT_CLIP_MODEL,
        top_k=10,
        min_similarity=0.2,
    )
    assert params["top_k"] > 0
    assert params["top_k"] <= 20
    assert 0.0 <= params["min_similarity"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
