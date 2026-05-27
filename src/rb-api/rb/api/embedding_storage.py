"""
Interface for storing embeddings in the database.

This module provides an abstract interface and implementations for
persisting embeddings to various storage backends.
"""

from abc import ABC, abstractmethod
from typing import Protocol
from rb.api.database import TextEmbedding, ImageEmbedding, ImageSimilarityEmbedding


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

    def __init__(self, session, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__(session)
        self.model_name = model_name

    def _create_record(self, path: str, embedding: list[float]):
        return TextEmbedding(path=path, model_name=self.model_name, embedding=embedding)

    def has_embeddings_for_paths(self, paths: list[str]) -> bool:
        """Check if all given paths have embeddings for this model."""
        if not paths:
            return False
        from sqlmodel import select
        existing = self.session.exec(
            select(TextEmbedding.path).where(
                TextEmbedding.path.in_(paths),
                TextEmbedding.model_name == self.model_name,
            )
        ).all()
        return set(existing) == set(paths)

    def delete_by_paths(self, paths: list[str]) -> None:
        """Delete embeddings for the given paths (for re-embed on model change)."""
        from sqlmodel import delete
        self.session.execute(
            delete(TextEmbedding).where(
                TextEmbedding.path.in_(paths),
                TextEmbedding.model_name == self.model_name,
            )
        )


class ImageEmbeddingStorage(DatabaseEmbeddingStorage):
    """Storage implementation for image embeddings."""

    def save_embedding(
        self, path: str, embedding: list[float], *, content_sha256: str = ""
    ) -> None:
        record = ImageEmbedding(
            path=path, embedding=embedding, content_sha256=content_sha256
        )
        self.session.add(record)

    def _create_record(self, path: str, embedding: list[float]):
        return ImageEmbedding(path=path, embedding=embedding)


class ImageSimilarityEmbeddingStorage(DatabaseEmbeddingStorage):
    """Persists image embeddings for the image-similarity plugin, keyed by path and content hash."""

    def __init__(self, session, model_name: str = "google/siglip2-so400m-patch14-384"):
        super().__init__(session)
        self.model_name = model_name

    def save_embedding(
        self, path: str, embedding: list[float], *, content_sha256: str = ""
    ) -> None:
        self.session.add(ImageSimilarityEmbedding(
            path=path,
            embedding=embedding,
            content_sha256=content_sha256,
            model_name=self.model_name,
        ))

    def _create_record(self, path: str, embedding: list[float]):
        return ImageSimilarityEmbedding(
            path=path, embedding=embedding, model_name=self.model_name
        )


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
