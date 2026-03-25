from pgvector.sqlalchemy import Vector
from sqlalchemy import Text
from sqlmodel import Field, SQLModel, create_engine, Column, Index
import os

## Create the data model and connect to the DB

# Prefer env override; default to docker-compose service hostname 'db'
postgres_url = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://rbuser:rescue@127.0.0.1:5433/rescuebox",
)
engine = create_engine(postgres_url, pool_pre_ping=True, future=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    # Migration: add model_name to text_embeddings if missing (for existing DBs)
    try:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE text_embeddings ADD COLUMN model_name VARCHAR(128) DEFAULT 'all-MiniLM-L6-v2' NOT NULL")
            )
    except Exception:
        pass  # Column likely already exists
    # Migration: add chunk_size, chunk_overlap if missing (for config invalidation)
    try:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE text_embedding_chunks ADD COLUMN IF NOT EXISTS chunk_size INT DEFAULT 0"))
            conn.execute(text("ALTER TABLE text_embedding_chunks ADD COLUMN IF NOT EXISTS chunk_overlap INT DEFAULT 0"))
    except Exception:
        pass
    SQLModel.metadata.create_all(engine)
    # Recreate HNSW index for text_embedding_chunks (dropped with table)
    try:
        chunk_index = Index(
            "text_chunk_vector_idx",
            TextEmbeddingChunk.embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_l2_ops"},
        )
        chunk_index.create(engine)
    except Exception:
        pass  # Index may already exist


class TextEmbedding(SQLModel, table=True):
    __tablename__ = "text_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    model_name: str = Field(default="all-MiniLM-L6-v2", index=True)
    embedding: list[float] = Field(default=[], sa_column=Column(Vector(384)))

class TextEmbeddingChunk(SQLModel, table=True):
    """Chunk-level text embedding for better semantic recall (e.g. 'stones' matches 'pebbles')."""

    __tablename__ = "text_embedding_chunks"

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    chunk_index: int = Field(default=0)
    chunk_text: str = Field(default="", sa_column=Column(Text))
    model_name: str = Field(default="BAAI/bge-small-en-v1.5", index=True)
    chunk_size: int = Field(default=0)  # 0 = legacy; used to invalidate when params change
    chunk_overlap: int = Field(default=0)
    embedding: list[float] = Field(default=[], sa_column=Column(Vector(384)))


class ImageEmbedding(SQLModel, table=True):
    __tablename__ = "image_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    embedding: list[int] = Field(default=[], sa_column=Column(Vector(512)))

# TODO: There is probably a way to do this without this try kludge
try:
    # Create an HNSW index
    index = Index(
        'item_vector_idx',
        TextEmbedding.embedding,
        postgresql_using='hnsw',
        # OK, like, whatever...
        postgresql_with={'m': 16, 'ef_construction': 64},
        postgresql_ops={'embedding': 'vector_l2_ops'}
    )
    index.create(engine)

    chunk_index = Index(
        "text_chunk_vector_idx",
        TextEmbeddingChunk.embedding,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_l2_ops"},
    )
    chunk_index.create(engine)

    img_index = Index(
        'item_vector_idx',
        ImageEmbedding.embedding,
        postgresql_using='hnsw',
        # OK, like, whatever...
        postgresql_with={'m': 16, 'ef_construction': 64},
        postgresql_ops={'embedding': 'vector_l2_ops'}
    )
    img_index.create(engine)
except:
    print("Index probably already exists")
