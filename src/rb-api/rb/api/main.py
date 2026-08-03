import logging
import multiprocessing
import os
import sys
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from rb.api import (
    dll_paths,  # cuDNN/CUDA DLL path before onnxruntime import
    routes,
)
from rb.api.database import create_db_and_tables
from rb.api.facematch_request_context import FacematchRescueboxUserMiddleware
from rb.api.job_progress_middleware import JobProgressMiddleware

# Standalone API process: file logging before routes import (routes must not reconfigure).
from rb.api.logging_setup import backend_log_file_path, configure_backend_logging
import rb.lib.ollama  # noqa: F401

configure_backend_logging()
dll_paths.log_detected_dll_paths()

logger = logging.getLogger("rb.api.main")


# 1. Safely set the cache paths FIRST
# local_appdata = os.getenv("APPDATA", os.path.expanduser("~"))
# app_cache_dir = Path(local_appdata) / "RescueBox"
# os.environ["XDG_CACHE_HOME"] = str(app_cache_dir / "xdg_cache")


def _run_startup() -> None:
    # Uvicorn's default log_config runs in Config() before the app is imported; it can
    # interact badly with root handlers. We pass log_config=None in uvicorn.run below so
    # dictConfig is skipped; re-apply our file + stderr handlers here anyway.
    configure_backend_logging()
    dll_paths.log_detected_dll_paths()
    log = logging.getLogger("rb.api")
    try:
        log.info("Creating database and tables")
        create_db_and_tables()
    except Exception as exc:
        log.exception("Startup failed while creating database tables: %s", exc)
        raise
    from rb.lib.job_progress import progress_dir

    if "RESCUEBOX_PROGRESS_DIR" not in os.environ:
        os.environ["RESCUEBOX_PROGRESS_DIR"] = str(progress_dir())
    else:
        progress_dir()
    log.info("Job progress directory: %s", progress_dir())
    log.info(
        "RescueBox API ready. set RESCUEBOX_API_LOG_LEVEL=DEBUG for full trace. "
        "Log file: %s",
        backend_log_file_path(),
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _run_startup()
    yield


app = FastAPI(
    title="RescueBoxAPI",
    summary="RescueBox is a set of tools for file system investigations.",
    version="3.0.0",
    debug=True,
    contact={
        "name": "Umass Amherst RescuBox Team",
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
app.add_middleware(FacematchRescueboxUserMiddleware)
app.add_middleware(JobProgressMiddleware)


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
