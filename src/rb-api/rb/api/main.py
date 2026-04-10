import multiprocessing
import os
import sys

# Standalone API process: file logging before routes import (routes must not reconfigure).
from rb.api.logging_setup import configure_backend_logging

configure_backend_logging()

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rb.api import routes
from rb.api.facematch_request_context import FacematchRescueboxUserMiddleware
from rb.api.database import create_db_and_tables

app = FastAPI(
    title="RescueBoxAPI",
    summary="RescueBox is a set of tools for file system investigations.",
    version="3.0.0",
    debug=True,
    contact={
        "name": "Umass Amherst RescuBox Team",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
app.add_middleware(FacematchRescueboxUserMiddleware)

@app.on_event("startup")
def on_startup():
    # Uvicorn applies dictConfig after import; re-apply our root handlers so
    # plugin and cli DEBUG/INFO lines keep going to file + stderr.
    configure_backend_logging()
    print("Creating database and tables")
    create_db_and_tables()

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):  # fmt: skip
    """response handler for all plugin input validation errors"""
    error_msg = str(exc)
    for e in exc.errors():
        error_msg = e.get("msg")

    raise HTTPException(  # pylint: disable=raise-missing-from
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"error": f"{error_msg}"},
    )


app.include_router(routes.probes_router, prefix="/probes")
app.include_router(routes.cli_to_api_router)
# Match unified frontend app (frontend/main.py): /api/models, /api/servers, etc.
app.include_router(routes.models_router, prefix="/api")
app.include_router(routes.ui_router)


if __name__ == "__main__":
    import uvicorn

    multiprocessing.freeze_support()  # For Windows support
    # for pyinstaller exe
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    else:
        # for cmdline dev mode
        uvicorn.run("rb.api.main:app", host="127.0.0.1", port=8000, reload=False)
