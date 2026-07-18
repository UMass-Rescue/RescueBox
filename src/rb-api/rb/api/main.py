import logging
import multiprocessing
import os
import sys
import traceback
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from rb.api import routes
from rb.api.facematch_request_context import FacematchRescueboxUserMiddleware
from rb.api.database import create_db_and_tables

# Standalone API process: file logging before routes import (routes must not reconfigure).
from rb.api.logging_setup import configure_backend_logging

configure_backend_logging()
logger = logging.getLogger("rb.api.main")


# 1. Safely set the cache paths FIRST
# local_appdata = os.getenv("APPDATA", os.path.expanduser("~"))
# app_cache_dir = Path(local_appdata) / "RescueBox"
# os.environ["XDG_CACHE_HOME"] = str(app_cache_dir / "xdg_cache")

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
    log = logging.getLogger("rb.api")
    try:
        log.info("Creating database and tables")
        create_db_and_tables()
    except Exception as exc:
        log.exception("Startup failed while creating database tables: %s", exc)
        raise
    log.info(
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Log and return JSON for unexpected errors (HTTP/validation use handlers above)."""
    if isinstance(exc, HTTPException):
        raise exc
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
    )
    detail = str(exc) if app.debug else "An unexpected error occurred."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": detail},
    )


app.include_router(routes.probes_router, prefix="/probes")
app.include_router(routes.cli_to_api_router)
# Match unified frontend app (frontend/main.py): /api/models, /api/servers, etc.
app.include_router(routes.models_router, prefix="/api")
app.include_router(routes.ui_router)


if __name__ == "__main__":
    import uvicorn

    multiprocessing.freeze_support()  # For Windows support

    def _run_api() -> None:
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

    try:
        _run_api()
    except Exception:
        logger.critical(
            "RescueBox API process exited with an error:\n%s", traceback.format_exc()
        )
        sys.exit(1)
