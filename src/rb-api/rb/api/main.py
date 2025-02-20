import multiprocessing
import os
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from logging.config import dictConfig
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from rb.api import routes

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",

        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "foo-logger": {"handlers": ["default"], "level": "DEBUG"},
    },
}
dictConfig(log_config)



class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logging.debug(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logging.debug(f"Response: {response.status_code}")
        return response

      

app = FastAPI(
    title="RescueBoxAPI",
    summary="RescueBox is a set of tools for file system investigations.",
    version="0.1.0",
    debug=True,
    contact={
        "name": "Umass Amherst RescuBox Team",
    },
)

app.add_middleware(LogMiddleware)  

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

app.include_router(routes.probes_router, prefix="/probes")
app.include_router(routes.cli_to_api_router)
app.include_router(routes.ui_router)




if __name__ == "__main__":
    import uvicorn

    multiprocessing.freeze_support()  # For Windows support

    uvicorn.run("rb.api.main:app", host="0.0.0.0", port=8000, reload=True)
