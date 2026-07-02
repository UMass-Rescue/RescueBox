from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text
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
                text(
                    "ALTER TABLE text_embeddings ADD COLUMN model_name VARCHAR(128) DEFAULT 'BAAI/bge-m3' NOT NULL"
                )
            )
    except Exception:
        pass  # Column likely already exists
    # Migration: add chunk_size, chunk_overlap if missing (for config invalidation)
    try:
        from sqlalchemy import text

        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE text_embedding_chunks ADD COLUMN IF NOT EXISTS chunk_size INT DEFAULT 0"
                )
            )
            conn.execute(
                text(
                    "ALTER TABLE text_embedding_chunks ADD COLUMN IF NOT EXISTS chunk_overlap INT DEFAULT 0"
                )
            )
    except Exception:
        pass
    try:
        from sqlalchemy import text

        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE image_embeddings ADD COLUMN IF NOT EXISTS "
                    "content_sha256 VARCHAR(64) DEFAULT '' NOT NULL"
                )
            )
    except Exception:
        pass
    # BGE-M3 and other modern text encoders use 1024-dim vectors; legacy was 384 (MiniLM / bge-small).
    try:
        from sqlalchemy import text

        with engine.begin() as conn:
            for table, idx_name in (
                ("text_embedding_chunks", "text_chunk_vector_idx"),
                ("text_embeddings", "item_vector_idx"),
            ):
                row = conn.execute(
                    text(
                        "SELECT format_type(a.atttypid, a.atttypmod) AS t "
                        "FROM pg_attribute a "
                        "JOIN pg_class c ON a.attrelid = c.oid "
                        "WHERE c.relname = :tname AND a.attname = 'embedding' "
                        "AND NOT a.attisdropped"
                    ),
                    {"tname": table},
                ).fetchone()
                if row and row[0] and "(1024)" not in str(row[0]):
                    conn.execute(text(f"DROP INDEX IF EXISTS {idx_name}"))
                    conn.execute(text(f"DELETE FROM {table}"))
                    conn.execute(text(f"ALTER TABLE {table} DROP COLUMN embedding"))
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN embedding vector(1024)")
                    )
    except Exception:
        pass

    # Image embeddings: plugin default openai/clip-vit-large-patch14-336 → projection_dim 768.
    try:
        from sqlalchemy import text

        with engine.begin() as conn:
            row = conn.execute(
                text(
                    "SELECT format_type(a.atttypid, a.atttypmod) AS t "
                    "FROM pg_attribute a "
                    "JOIN pg_class c ON a.attrelid = c.oid "
                    "WHERE c.relname = 'image_embeddings' AND a.attname = 'embedding' "
                    "AND NOT a.attisdropped"
                )
            ).fetchone()
            if row and row[0] and "(768)" not in str(row[0]):
                conn.execute(text("DROP INDEX IF EXISTS image_embeddings_hnsw_idx"))
                conn.execute(text("DELETE FROM image_embeddings"))
                conn.execute(text("ALTER TABLE image_embeddings DROP COLUMN embedding"))
                conn.execute(
                    text(
                        "ALTER TABLE image_embeddings ADD COLUMN embedding vector(512))"
                    )
                )
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
    try:
        img_index = Index(
            "image_embeddings_hnsw_idx",
            ImageEmbedding.embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_l2_ops"},
        )
        img_index.create(engine)
    except Exception:
        pass  # Index may already exist
    try:
        face_index = Index(
            "face_embeddings_hnsw_idx",
            FaceEmbedding.embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        )
        face_index.create(engine)
    except Exception:
        pass


class TextEmbedding(SQLModel, table=True):
    __tablename__ = "text_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    model_name: str = Field(default="all-MiniLM-L6-v2", index=True)
    embedding: list[float] = Field(default=[], sa_column=Column(Vector(1024)))


class TextEmbeddingChunk(SQLModel, table=True):
    """Chunk-level text embedding for better semantic recall (e.g. 'stones' matches 'pebbles')."""

    __tablename__ = "text_embedding_chunks"

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    chunk_index: int = Field(default=0)
    chunk_text: str = Field(default="", sa_column=Column(Text))
    model_name: str = Field(default="BAAI/bge-small-en-v1.5", index=True)
    chunk_size: int = Field(
        default=0
    )  # 0 = legacy; used to invalidate when params change
    chunk_overlap: int = Field(default=0)
    embedding: list[float] = Field(default=[], sa_column=Column(Vector(1024)))


class ImageEmbedding(SQLModel, table=True):
    __tablename__ = "image_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    # SHA-256 hex of file bytes; reuse embeddings when path changes but content matches.
    content_sha256: str = Field(default="", index=True)
    # CLIP ViT-L/14 @336px joint embedding size (must match image_embeddings plugin default projection_dim).
    embedding: list[float] = Field(default=[], sa_column=Column(Vector(512)))


class ImageSimilarityEmbedding(SQLModel, table=True):
    """Image embeddings used by the image-to-image similarity search plugin."""

    __tablename__ = "image_similarity_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    content_sha256: str = Field(default="", sa_column=Column(String(64), index=True))
    model_name: str = Field(
        default="google/siglip2-so400m-patch14-384",
        sa_column=Column(String(128), index=True),
    )
    embedding: list[float] = Field(default=[], sa_column=Column(Vector(1152)))
    pdq_hash: str = Field(default="", sa_column=Column(String(64), index=True))


class FaceEmbedding(SQLModel, table=True):
    """Face-match plugin embeddings (replaces per-scope Chroma collections)."""

    __tablename__ = "face_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    # Isolation key (demo folder, RescueBox user hash, or "" for legacy default).
    scope: str = Field(default="", index=True)
    # Full collection name, e.g. sample_refa512S (includes detector/model/ensemble suffix).
    collection_name: str = Field(index=True)
    # Stable face id (sha256 of image path + bbox); was Chroma document id.
    face_id: str = Field(index=True)
    image_path: str = Field(index=True)
    # Facenet512 / ArcFace default output size.
    embedding: list[float] = Field(default=[], sa_column=Column(Vector(512)))


# TODO: There is probably a way to do this without this try kludge
try:
    # Create an HNSW index
    index = Index(
        "item_vector_idx",
        TextEmbedding.embedding,
        postgresql_using="hnsw",
        # OK, like, whatever...
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_l2_ops"},
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
        "image_embeddings_hnsw_idx",
        ImageEmbedding.embedding,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_l2_ops"},
    )
    img_index.create(engine)

    face_index = Index(
        "face_embeddings_hnsw_idx",
        FaceEmbedding.embedding,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    face_index.create(engine)
except Exception:
    print("Index probably already exists")
