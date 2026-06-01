"""Tests for embedding storage interface."""

import pytest
from rb.api.embedding_storage import (
    NoOpEmbeddingStorage,
)


def test_noop_storage():
    """Test that NoOpEmbeddingStorage doesn't raise errors."""
    storage = NoOpEmbeddingStorage()
    
    # Should not raise any exceptions
    storage.save_embedding("/path/to/file.txt", [0.1, 0.2, 0.3])
    storage.save_batch({
        "/path/1.txt": [0.1, 0.2],
        "/path/2.txt": [0.3, 0.4],
    })
    storage.commit()


def test_storage_interface():
    """Test that storage classes have the required interface."""
    # Verify the interface exists
    noop = NoOpEmbeddingStorage()
    assert hasattr(noop, 'save_embedding')
    assert hasattr(noop, 'save_batch')
    assert hasattr(noop, 'commit')
    assert callable(noop.save_embedding)
    assert callable(noop.save_batch)
    assert callable(noop.commit)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
