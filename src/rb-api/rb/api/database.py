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

app = FastAPI(
    title="RescueBoxAPI",
    summary="RescueBox is a set of tools for file system investigations.",
    version="2.0.0",
    debug=True,
    contact={
        "name": "Umass Amherst RescuBox Team",
    },
)

@app.on_event("startup")
def on_startup():
    print("Creating database and tables")
    create_db_and_tables()
