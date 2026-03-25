"""Tests for image embeddings search functionality."""

import pytest
from image_embeddings.main import search_images, search_task_schema, SearchInputs, SearchParameters
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
    assert callable(search_images)
    
    # Verify the function signature
    import inspect
    sig = inspect.signature(search_images)
    assert "inputs" in sig.parameters
    assert "parameters" in sig.parameters


def test_search_inputs_structure():
    """Test that SearchInputs has correct structure."""
    inputs = SearchInputs(query=TextInput(text="a cat on a couch"))
    assert "query" in inputs
    assert inputs["query"].text == "a cat on a couch"


def test_search_parameters_structure():
    """Test that SearchParameters has correct structure."""
    params = SearchParameters(model_name="openai/clip-vit-base-patch32", top_k=5)
    assert params["model_name"] == "openai/clip-vit-base-patch32"
    assert params["top_k"] == 5


def test_cross_modal_search_concept():
    """Test that search uses text input to find images (conceptual test)."""
    # This is a conceptual test verifying the cross-modal nature
    # The actual search would require database setup
    inputs = SearchInputs(query=TextInput(text="sunset over ocean"))
    params = SearchParameters(model_name="openai/clip-vit-base-patch32", top_k=10)
    
    # Verify inputs are text-based
    assert isinstance(inputs["query"], TextInput)
    assert isinstance(inputs["query"].text, str)
    
    # Verify we're searching for multiple results
    assert params["top_k"] > 0
    assert params["top_k"] <= 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
