from pgvector.sqlalchemy import Vector
from sqlmodel import Field, SQLModel, create_engine, Column, Index
import os

## Create the data model and connect to the DB

# Prefer env override; default to docker-compose service hostname 'db'
postgres_url = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://rbuser:rescue@db:5432/rescuebox",
)
engine = create_engine(postgres_url, pool_pre_ping=True, future=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


class TextEmbedding(SQLModel, table=True):
    __tablename__ = "text_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    embedding: list[float] = Field(default=[], sa_column=Column(Vector(384)))

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
except:
    print("Index probably already exists")