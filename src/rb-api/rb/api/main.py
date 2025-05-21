import json
import multiprocessing
import os
import sys
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from rb.api import routes

app = FastAPI(
    title="RescueBoxAPI",
    summary="RescueBox is a set of tools for file system investigations.",
    version="0.1.0",
    debug=True,
    contact={
        "name": "Umass Amherst RescuBox Team",
    },
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
app.include_router(routes.ui_router)


# https://fastapi.tiangolo.com/how-to/extending-openapi/#overriding-the-defaults
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="RescueBoxAPI",
        version="1.1.0",
        summary="This is a recuebox OpenAPI schema",
        description="recuebox OpenAPI schema for plugins **OpenAPI** schema",
        routes=app.routes
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://github.com/UMass-Rescue/RescueBox/tree/main/RescueBox-Desktop/assets/icon.png"
    }

    trim_schema_names = {}
    for route in app.routes:
        if route.name != 'static':
            # print(f"plugin route name is {route.path}, {route.methods}")
            name = str(route.path.replace('-','_').replace("/", "_"))
            method = str('_') + str(route.methods.pop().lower())
            key = name + method
            value = method
            trim_schema_names[key] = value

    # Dict to json string, replace the schema name, and back to dict
    for schema_name, replacement in trim_schema_names.items():
        openapi_schema = json.loads(json.dumps(openapi_schema).replace(schema_name, replacement))

    # Sort the components schemas, because new name could not be sorted correctly
    openapi_schema['components']['schemas'] = dict(sorted(openapi_schema['components']['schemas'].items()))

    app.openapi_schema = openapi_schema

    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn

    multiprocessing.freeze_support()  # For Windows support
    # for pyinstaller exe
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    else:
        # for cmdline dev mode
        uvicorn.run("rb.api.main:app", host="0.0.0.0", port=8000, reload=True)
