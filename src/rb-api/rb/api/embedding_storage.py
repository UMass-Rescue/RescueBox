"""
Interface for storing embeddings in the database.

This module provides an abstract interface and implementations for
persisting embeddings to various storage backends.
"""

from abc import ABC, abstractmethod
from typing import Protocol
from rb.api.database import TextEmbedding, ImageEmbedding


class EmbeddingStorage(Protocol):
    """Protocol for embedding storage implementations."""
    
    def save_embedding(self, path: str, embedding: list[float]) -> None:
        """
        Save a single embedding to storage.
        
        Args:
            path: File path associated with the embedding
            embedding: The embedding vector as a list of floats
        """
        ...
    
    def save_batch(self, embeddings: dict[str, list[float]]) -> None:
        """
        Save multiple embeddings to storage in a batch.
        
        Args:
            embeddings: Dictionary mapping file paths to embedding vectors
        """
        ...
    
    def commit(self) -> None:
        """Commit any pending changes to storage."""
        ...


class DatabaseEmbeddingStorage:
    """
    Base class for database-backed embedding storage.
    
    Provides transaction management and batch operations using SQLModel sessions.
    """
    
    def __init__(self, session):
        """
        Initialize storage with a database session.
        
        Args:
            session: SQLModel Session instance
        """
        self.session = session
        self._pending_records = []
    
    @abstractmethod
    def _create_record(self, path: str, embedding: list[float]):
        """
        Create a database record for the embedding.
        
        Args:
            path: File path
            embedding: Embedding vector
            
        Returns:
            Database model instance
        """
        raise NotImplementedError
    
    def save_embedding(self, path: str, embedding: list[float]) -> None:
        """Save a single embedding to the session."""
        record = self._create_record(path, embedding)
        self.session.add(record)
    
    def save_batch(self, embeddings: dict[str, list[float]]) -> None:
        """Save multiple embeddings to the session."""
        for path, embedding in embeddings.items():
            self.save_embedding(path, embedding)
    
    def commit(self) -> None:
        """Commit all pending changes to the database."""
        self.session.commit()


class TextEmbeddingStorage(DatabaseEmbeddingStorage):
    """Storage implementation for text embeddings."""
    
    def _create_record(self, path: str, embedding: list[float]):
        return TextEmbedding(path=path, embedding=embedding)


class ImageEmbeddingStorage(DatabaseEmbeddingStorage):
    """Storage implementation for image embeddings."""
    
    def _create_record(self, path: str, embedding: list[float]):
        return ImageEmbedding(path=path, embedding=embedding)


class NoOpEmbeddingStorage:
    """
    No-operation storage for testing or when persistence is not needed.
    """
    
    def save_embedding(self, path: str, embedding: list[float]) -> None:
        """No-op save."""
        pass
    
    def save_batch(self, embeddings: dict[str, list[float]]) -> None:
        """No-op batch save."""
        pass
    
    def commit(self) -> None:
        """No-op commit."""
        pass
