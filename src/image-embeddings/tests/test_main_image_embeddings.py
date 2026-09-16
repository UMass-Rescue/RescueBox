"""Tests for image embeddings plugin"""

import pytest
from image_embeddings.main import (
    DEFAULT_CLIP_MODEL,
    ClipImageDirectory,
    Inputs,
    Parameters,
    search_images,
    task_schema,
)
from rb.api.models import TextInput


def test_task_schema():
    """Test task schema keys."""
    schema = task_schema()
    assert schema is not None
    assert len(schema.inputs) == 2
    assert schema.inputs[0].key == "input_dir"
    assert schema.inputs[1].key == "query"
    assert len(schema.parameters) == 3
    keys = [p.key for p in schema.parameters]
    assert keys == ["model_name", "top_k", "min_similarity"]


def test_search_images_types():
    """Test input/output types"""
    assert callable(search_images)

    import inspect

    sig = inspect.signature(search_images)
    assert "inputs" in sig.parameters
    assert "parameters" in sig.parameters


def test_inputs_structure(tmp_path):
    d = tmp_path / "img"
    d.mkdir()
    (d / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    inputs = Inputs(
        input_dir=ClipImageDirectory(path=d),
        query=TextInput(text="a person"),
    )
    assert inputs["query"].text == "a person"


def test_parameters_structure():
    params = Parameters(
        model_name=DEFAULT_CLIP_MODEL,
        top_k=5,
        min_similarity=0.25,
    )
    assert params["top_k"] == 5
    assert params["min_similarity"] == 0.25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
