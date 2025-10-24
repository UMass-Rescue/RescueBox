import multiprocessing
import os
import ssl
import sys
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
sys.path.append("rb/api/routes")
from rb.api import routes

# Create some sort of offline config file to save keys securely
from config import CERT_PATH, KEY_PATH

app = FastAPI(
    title="RescueBoxAPI",
    summary="RescueBox is a set of tools for file system investigations.",
    version="2.0.0",
    debug=True,
    contact={
        "name": "Umass Amherst RescueBox Team",
    },
)

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)

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
app.include_router(routes.ui_router)


if __name__ == "__main__":
    import uvicorn

    multiprocessing.freeze_support()  # For Windows support
    # for pyinstaller exe
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, ssl=ssl_context)
    else:
        # for cmdline dev mode
        uvicorn.run("rb.api.main:app", host="0.0.0.0", port=8000, reload=True, ssl=ssl_context)
