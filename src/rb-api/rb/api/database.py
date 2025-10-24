from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

## Create the data model and connect to the DB

# TODO: Probably can relocate this to a better location, but for now...

# TODO: Need to think about credentials
postgres_url = "postgresql://dage@localhost/rescue_box"
engine = create_engine(postgres_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

class TempMediaCollection(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    # created_at: 
    # updated_at

## End database glue
