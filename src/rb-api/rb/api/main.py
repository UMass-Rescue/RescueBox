import multiprocessing
import os, sys
if sys.stdout is None:
    f = open(r"C:\work\out.log","w")
    #sys.stdout = open(os.devnull, "w")
    sys.stdout = f
if sys.stderr is None:
    f = open(r"C:\work\err.log","w")
    sys.stdout = f
    #sys.stderr = open(os.devnull, "w")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from rb.api import routes
import uvicorn
import logging

app = FastAPI(
    title="RescueBoxAPI",
    summary="RescueBox is a set of tools for file system investigations.",
    version="0.1.0",
    debug = True,
    contact={
        "name": "Jagath Jai Kumar",
    },
)

logger = logging.getLogger('uvicorn.error')
logger.propagate = True
logger.setLevel(logging.DEBUG)

@app.get('/log')
async def main():
    logger.debug('this is a debug message')
    return 'log ok'

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
    # use_colors=False
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
