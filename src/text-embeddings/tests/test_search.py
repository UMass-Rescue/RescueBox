"""Tests for text embeddings search functionality."""

import pytest
from text_embeddings.main import search, task_schema, Inputs, Parameters
from rb.api.models import TextInput, DirectoryInput
from pathlib import Path


def test_search_task_schema():
    """Test that search task schema is properly defined."""
    schema = task_schema()
    assert schema is not None
    assert len(schema.inputs) == 3
    assert schema.inputs[0].key == "input_dir"
    assert schema.inputs[1].key == "query"
    assert schema.inputs[2].key == "file_filter"
    assert len(schema.parameters) == 2
    assert schema.parameters[0].key == "top_k"
    assert schema.parameters[1].key == "min_similarity"


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
