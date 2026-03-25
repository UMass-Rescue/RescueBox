"""Tests for image embeddings plugin"""

import pytest
from pathlib import Path
from image_embeddings.main import embed_images, task_schema, Inputs, Parameters
from rb.api.models import DirectoryInput, ResponseBody


def test_task_schema():
    """Test that task schema is properly defined"""
    schema = task_schema()
    assert schema is not None
    assert len(schema.inputs) == 1
    assert schema.inputs[0].key == "input_dir"
    assert len(schema.parameters) == 1
    assert schema.parameters[0].key == "model_name"


def test_embed_images_types():
    """Test input/output types"""
    # This test verifies the function signature without running it
    # since we don't have test images readily available
    assert callable(embed_images)
    
    # Verify the function takes correct types
    import inspect
    sig = inspect.signature(embed_images)
    assert "inputs" in sig.parameters
    assert "parameters" in sig.parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
