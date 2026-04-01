"""Tests for image embeddings plugin"""

import pytest
from image_embeddings.main import search_images, task_schema, Inputs, Parameters
from rb.api.models import DirectoryInput, TextInput, ResponseBody


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
    inputs = Inputs(
        input_dir=DirectoryInput(path=d),
        query=TextInput(text="a person"),
    )
    assert inputs["query"].text == "a person"


def test_parameters_structure():
    params = Parameters(
        model_name="openai/clip-vit-base-patch32",
        top_k=5,
        min_similarity=0.25,
    )
    assert params["top_k"] == 5
    assert params["min_similarity"] == 0.25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
