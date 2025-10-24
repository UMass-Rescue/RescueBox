from pgvector.sqlalchemy import Vector
from sqlmodel import Field, SQLModel, create_engine, Column

## Create the data model and connect to the DB

# Note:
#
# Installation needs to enforce a shared username across deployments.
# Furthermore, installing postgresql with Rescue Box may be its own task,
# requiring consideration for if PG happens to already be installed, etc...
#
postgres_url = "postgresql://prasannals@localhost/rescue_box"
engine = create_engine(postgres_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

class TextEmbedding(SQLModel, table=True):
    __tablename__ = "text_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    embedding: list[int] = Field(default=[], sa_column=Column(Vector(384)))

class ImageEmbedding(SQLModel, table=True):
    __tablename__ = "image_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    embedding: list[int] = Field(default=[], sa_column=Column(Vector(512)))
