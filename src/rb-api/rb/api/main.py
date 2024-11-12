import multiprocessing
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from rb.api import routes

app = FastAPI(
    title="RescueBoxAPI",
    summary="RescueBox is a set of tools for file system investigations.",
    version="0.1.0",
    contact={
        "name": "Jagath Jai Kumar",
    },
)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

app.include_router(routes.probes_router, prefix="/probes")
app.include_router(routes.cli_router)
app.include_router(routes.ui_router)

if __name__ == "__main__":
    import uvicorn

    multiprocessing.freeze_support()  # For Windows support

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
