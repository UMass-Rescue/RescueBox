import json
import multiprocessing
import os
import sys
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from rb.api import routes
#from pipeline.rescuebox_pipeline.rb_celery import app as celery_app


def run_celery_worker():
    celery_app.worker_main(
        argv=[
            'worker',
            '--loglevel=DEBUG',
            '--pool=gevent',
        ]
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the worker on startup
    #celery_thread = threading.Thread(target=run_celery_worker, daemon=True)
    #celery_thread.start()
    #yield
    # No specific shutdown logic needed for the daemon thread
    yield

app = FastAPI(
    title="RescueBoxAPI",
    summary="RescueBox is a set of tools for file system investigations.",
    version="2.0.0",
    debug=True,
    contact={
        "name": "Umass Amherst RescuBox Team",
    },
    lifespan=lifespan
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


# https://fastapi.tiangolo.com/how-to/extending-openapi/#overriding-the-defaults
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="RescueBoxAPI",
        version="2.1.0",
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
            print(f"plugin route name is {route.path}, {route.methods}")
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

    # Pre-check for necessary keys
    if "paths" not in openapi_schema or "components" not in openapi_schema or "schemas" not in openapi_schema["components"]:
        raise ValueError("OpenAPI schema is missing required keys.")

    component_schemas = openapi_schema["components"]["schemas"]

    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, op in path_item.items():
            if "requestBody" not in op:
                continue
            
            try:
                # Get the schema for the request body content
                body_content_schema = op["requestBody"]["content"]["application/json"]["schema"]
            except KeyError:
                continue

            # Resolve the body schema to find its properties
            body_schema_props = None
            if "$ref" in body_content_schema:
                # Case 1: The schema is a reference, e.g., "$ref": "#/components/schemas/Body_..."
                ref_key = body_content_schema["$ref"].split('/')[-1]
                if ref_key in component_schemas and "properties" in component_schemas[ref_key]:
                    body_schema_props = component_schemas[ref_key]["properties"]
            elif "properties" in body_content_schema:
                # Case 2: The schema is defined inline and has properties directly
                body_schema_props = body_content_schema["properties"]

            if not body_schema_props:
                continue

            # Now that we have the properties ('inputs', 'parameters'), find the schemas they refer to
            for prop_name, prop_def in body_schema_props.items():
                if "$ref" not in prop_def:
                    continue
                
                final_ref_key = prop_def["$ref"].split('/')[-1]

                if final_ref_key not in component_schemas:
                    continue
                
                schema_def = component_schemas[final_ref_key]

                # If the title is generic, create a new unique one from the path
                if schema_def.get("title") in ["Inputs", "Parameters"]:
                    path_parts = path.strip('/').replace('-', '_').split('/')
                    new_title_base = "".join(word.capitalize() for part in path_parts for word in part.split('_'))
                    
                    original_title = schema_def["title"]
                    schema_def["title"] = f"{new_title_base}{original_title}"

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.include_router(routes.probes_router, prefix="/probes")
app.include_router(routes.cli_to_api_router)
app.include_router(routes.ui_router)


if __name__ == "__main__":
    import uvicorn

    multiprocessing.freeze_support()  # For Windows support
    # for pyinstaller exe
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    else:
        # for cmdline dev mode
        uvicorn.run("rb.api.main:app", host="0.0.0.0", port=8000, reload=True, workers=4)
