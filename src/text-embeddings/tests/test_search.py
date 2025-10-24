"""Tests for text embeddings search functionality."""

import pytest
from text_embeddings.main import search_text, search_task_schema, SearchInputs, SearchParameters
from rb.api.models import TextInput


def test_search_task_schema():
    """Test that search task schema is properly defined."""
    schema = search_task_schema()
    assert schema is not None
    assert len(schema.inputs) == 1
    assert schema.inputs[0].key == "query"
    assert len(schema.parameters) == 2
    assert schema.parameters[0].key == "model_name"
    assert schema.parameters[1].key == "top_k"


def test_search_types():
    """Test search input/output types."""
    assert callable(search_text)
    
    # Verify the function signature
    import inspect
    sig = inspect.signature(search_text)
    assert "inputs" in sig.parameters
    assert "parameters" in sig.parameters


def test_search_inputs_structure():
    """Test that SearchInputs has correct structure."""
    inputs = SearchInputs(query=TextInput(text="test query"))
    assert "query" in inputs
    assert inputs["query"].text == "test query"


def test_search_parameters_structure():
    """Test that SearchParameters has correct structure."""
    params = SearchParameters(model_name="all-MiniLM-L6-v2", top_k=5)
    assert params["model_name"] == "all-MiniLM-L6-v2"
    assert params["top_k"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
