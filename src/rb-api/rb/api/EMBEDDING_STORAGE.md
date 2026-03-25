# Embedding Storage Interface

This module provides a clean interface for storing embeddings in the database, promoting separation of concerns and making the code more testable.

## Architecture

### Protocol-Based Design

The `EmbeddingStorage` protocol defines the contract that all storage implementations must follow:

```python
class EmbeddingStorage(Protocol):
    def save_embedding(self, path: str, embedding: list[float]) -> None:
        """Save a single embedding."""
        
    def save_batch(self, embeddings: dict[str, list[float]]) -> None:
        """Save multiple embeddings in a batch."""
        
    def commit(self) -> None:
        """Commit changes to storage."""
```

### Implementations

#### 1. DatabaseEmbeddingStorage (Base Class)

Abstract base class providing common functionality for database-backed storage:
- Session management
- Transaction handling
- Batch operations

#### 2. TextEmbeddingStorage

Stores text embeddings in the `text_embeddings` table.

**Usage:**
```python
from rb.api.database import engine
from rb.api.embedding_storage import TextEmbeddingStorage
from sqlmodel import Session

with Session(engine) as session:
    storage = TextEmbeddingStorage(session)
    storage.save_embedding("/path/to/file.txt", [0.1, 0.2, ...])
    storage.commit()
```

#### 3. ImageEmbeddingStorage

Stores image embeddings in the `image_embeddings` table.

**Usage:**
```python
from rb.api.database import engine
from rb.api.embedding_storage import ImageEmbeddingStorage
from sqlmodel import Session

with Session(engine) as session:
    storage = ImageEmbeddingStorage(session)
    storage.save_embedding("/path/to/image.jpg", [0.3, 0.4, ...])
    storage.commit()
```

#### 4. NoOpEmbeddingStorage

No-operation implementation for testing or when persistence is not needed.

**Usage:**
```python
from rb.api.embedding_storage import NoOpEmbeddingStorage

storage = NoOpEmbeddingStorage()
storage.save_embedding("/path/to/file", [0.1, 0.2])  # Does nothing
storage.commit()  # Does nothing
```

## Benefits

### 1. Separation of Concerns
- Embedding generation logic is decoupled from storage logic
- Each component has a single responsibility

### 2. Testability
- Easy to inject mock/no-op storage for unit tests
- Can test embedding generation without database

### 3. Flexibility
- Easy to add new storage backends (e.g., Redis, filesystem)
- Can swap implementations without changing plugin code

### 4. Type Safety
- Protocol ensures all implementations have the same interface
- Type checkers can verify correct usage

## Integration with Plugins

Both `text-embeddings` and `image-embeddings` plugins use this interface:

```python
def embed_text(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    # ... setup code ...
    
    with Session(engine) as session:
        storage = TextEmbeddingStorage(session)
        
        for path in file_paths:
            # ... generate embedding ...
            storage.save_embedding(path, embedding)
        
        storage.commit()  # Atomic commit of all embeddings
```

## Extending the Interface

To add a new storage backend:

1. Implement the `EmbeddingStorage` protocol:
```python
class CustomStorage:
    def save_embedding(self, path: str, embedding: list[float]) -> None:
        # Your implementation
        
    def save_batch(self, embeddings: dict[str, list[float]]) -> None:
        # Your implementation
        
    def commit(self) -> None:
        # Your implementation
```

2. Use it in your plugin:
```python
storage = CustomStorage()
storage.save_embedding(path, embedding)
```

## Database Schema

The interface assumes the following database schema:

### text_embeddings table
- `id`: Primary key
- `path`: File path (indexed)
- `embedding`: Vector(384) - for sentence-transformers models

### image_embeddings table
- `id`: Primary key
- `path`: File path (indexed)
- `embedding`: Vector(512) - for CLIP base model

**Note:** Vector dimensions must match the model's output size.
