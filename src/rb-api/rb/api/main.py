import multiprocessing
import os
import sys

if sys.stdout is None:
    f = open(r"out.log", "w")
    # sys.stdout = open(os.devnull, "w")
    sys.stdout = f
if sys.stderr is None:
    f = open(r"err.log", "w")
    sys.stdout = f
    # sys.stderr = open(os.devnull, "w")

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from rb.api import routes
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

app = FastAPI(
    title="RescueBoxAPI",
    summary="RescueBox is a set of tools for file system investigations.",
    version="0.1.0",
    debug=True,
    contact={
        "name": "Jagath Jai Kumar",
    },
)

logger = logging.getLogger("uvicorn.error")
logger.propagate = True
logger.setLevel(logging.DEBUG)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logging.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

@app.get("/log")
async def main():
    logger.debug("this is a debug message")
    return "log ok"


app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

app.include_router(routes.probes_router, prefix="/probes")
app.include_router(routes.cli_router)
app.include_router(routes.ui_router)
app.include_router(routes.plugin_router)


if __name__ == "__main__":
    import uvicorn

    multiprocessing.freeze_support()  # For Windows support
    # use_colors=False
    uvicorn.run(
        "src.rb-api.rb.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
    )
