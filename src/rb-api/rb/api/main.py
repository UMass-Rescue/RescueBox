import logging
import multiprocessing
import os
import sys
from pathlib import Path

# Standalone API process: file logging before routes import (routes must not reconfigure).
from rb.api.logging_setup import configure_backend_logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rb.api import routes
from rb.api.facematch_request_context import FacematchRescueboxUserMiddleware
from rb.api.database import create_db_and_tables

# 1. Safely set the cache paths FIRST
local_appdata = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
app_cache_dir = Path(local_appdata) / "RescueBox-Desktop"

os.environ["MPLCONFIGDIR"] = str(app_cache_dir / "matplotlib")
os.environ["XDG_CACHE_HOME"] = str(app_cache_dir / "xdg_cache")

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
    # Uvicorn's default log_config runs in Config() before the app is imported; it can
    # interact badly with root handlers. We pass log_config=None in uvicorn.run below so
    # dictConfig is skipped; re-apply our file + stderr handlers here anyway.
    configure_backend_logging()
    print("Creating database and tables")
    create_db_and_tables()
    logging.getLogger("rb.api").info(
        "RescueBox API ready "
        "set RESCUEBOX_API_LOG_LEVEL=DEBUG for full trace. "
        "API_LOG_FILE rb-backend.log"
    )


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
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_config=None,
            workers=1,
        )
    else:
        # log_config=None: do not let Uvicorn apply its default dictConfig (would run
        # before the app import and can leave application loggers disconnected from
        # the root handlers configured in configure_backend_logging).
        uvicorn.run(
            "rb.api.main:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_config=None,
            workers=1,
        )
