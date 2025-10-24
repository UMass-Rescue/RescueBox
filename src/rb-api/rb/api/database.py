from pgvector.sqlalchemy import Vector
from sqlmodel import Field, SQLModel, create_engine, Column

## Create the data model and connect to the DB

# Note:
#
# Installation needs to enforce a shared username across deployments.
# Furthermore, installing postgresql with Rescue Box may be its own task,
# requiring consideration for if PG happens to already be installed, etc...
#
postgres_url = "postgresql://rescue_box@localhost/rescue_box"
engine = create_engine(postgres_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

class MediaCollection(SQLModel, table=True):
    __tablename__ = "media_collections"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    embedding: list[int] = Field(default=None, sa_column=Column(Vector(3)))
    # created_at:
    # updated_at
