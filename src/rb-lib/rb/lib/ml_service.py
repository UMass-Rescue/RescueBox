import sys
from pathlib import Path

# This code manually adds the 'src' directory to the Python path.
# It finds the path to the current file, goes up three levels to get to the 'src' directory,
# and then adds it to the list of paths Python searches for modules.
# This ensures that modules like 'audio_transcription' can be found by the worker.
src_path = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(src_path))

from dataclasses import dataclass
from logging import getLogger
from typing import Any, Callable, List, Optional, get_type_hints, Annotated

from fastapi import Body
import typer
from celery.result import AsyncResult
from rescuebox_pipeline.rb_celery import app as rb_celery_app

from rb.api.models import (
    APIRoutes,
    ResponseBody,
    SchemaAPIRoute,
    TaskSchema,
    AppMetadata,
    TextResponse,
)
from rb.lib.utils import (
    ensure_ml_func_hinting_and_task_schemas_are_valid,
    ensure_ml_func_parameters_are_typed_dict,
)


logger = getLogger(__name__)

# Add a global registry for ML services
ML_REGISTRY = {}

# Add functions to get registered items
def get_ml_function(service_name: str):
    service = ML_REGISTRY.get(service_name)
    return service["function"] if service else None


def get_ml_schema_func(service_name: str):
    service = ML_REGISTRY.get(service_name)
    return service["schema_func"] if service else None


@dataclass
class EndpointDetailsNoSchema:
    rule: str
    func: Callable[..., ResponseBody]


@dataclass
class EndpointDetails(EndpointDetailsNoSchema):
    task_schema_rule: str
    task_schema_func: Callable[[], TaskSchema]
    short_title: str
    order: int
    help: str


class MLService(object):
    """
    The MLService object is a wrapper class for the app object. It
    provides a decorator for turning a machine learning prediction function
    into a rest api endpoint.
    """

    def __init__(self, name, help="model operation"):
        """
        Instantiates the MLService object as a wrapper for the app.
        """
        self.name = name
        self.app = typer.Typer()
        self.endpoints: List[EndpointDetails] = []
        self._app_metadata: Optional[AppMetadata] = None
        self.plugin_name = name
        self.help = help

        @self.app.command(f"/{self.name}/api/routes")
        def list_routes():
            """
            Lists all the routes/endpoints available in the app.
            """
            routes = [
                SchemaAPIRoute(
                    task_schema=endpoint.task_schema_rule,
                    run_task=endpoint.rule,
                    short_title=endpoint.short_title,
                    order=endpoint.order,
                )
                for endpoint in self.endpoints
            ]
            res = APIRoutes(root=routes).model_dump(mode="json")
            logger.info(res)
            return res

        logger.debug("Registered routes command: /api/routes")

        @self.app.command(f"/{self.name}/api/app_metadata")
        def get_app_metadata():
            if self._app_metadata is None:
                return {"error": "App metadata not set"}
            res = self._app_metadata.model_dump(mode="json")
            logger.info(res)
            return res

    def add_app_metadata(
        self,
        name: str,
        author: str,
        version: str,
        info: str,
        plugin_name: str,
        gpu: bool = False,
    ):
        self._app_metadata = AppMetadata(
            name=name,
            author=author,
            version=version,
            info=info,
            plugin_name=plugin_name,
            gpu=gpu,
        )

    def add_ml_service(
        self,
        rule: str,
        ml_function: Callable[[Any, Any], ResponseBody],
        inputs_cli_parser,
        parameters_cli_parser=None,
        task_schema_func: Optional[Callable[[], TaskSchema]] = None,
        short_title: Optional[str] = None,
        order: int = 0,
        is_workflow_step: bool = False,
        help: str = "model operation",
        is_async: bool = False,
    ):
        """
        Adds a machine learning service to the Typer app and exposes it as an API endpoint.

        Args:
            rule (str): The API rule for the endpoint (e.g., "/summarize").
            ml_function (Callable): The function that performs the ML task.
            inputs_cli_parser: The Typer parser for the input arguments.
            parameters_cli_parser: The Typer parser for the parameter arguments.
            task_schema_func (Optional): A function that returns the TaskSchema.
            short_title (Optional): A short title for the task.
            order (int): The display order for the task.
            help (str): The help text for the command.
            is_async (bool): If True, the service is treated as an asynchronous Celery task.
                             This enables a two-step asynchronous workflow:
                             1. The initial POST request to the main endpoint (e.g., `/transcribe`) starts the task
                                and immediately returns a 202 Accepted response with a `task_id`.
                             2. A separate GET endpoint, `/transcribe/result/{task_id}`, is created, which clients
                                can poll to check the task's status and retrieve the final result once it's ready.
        """
        global ML_REGISTRY
        ML_REGISTRY[f"{self.name}{rule}"] = {
            "function": ml_function,
            "schema_func": task_schema_func,
        }
        ensure_ml_func_parameters_are_typed_dict(ml_function)
        ensure_ml_func_hinting_and_task_schemas_are_valid(
            ml_function, task_schema_func()
        )
        processed_title = short_title or ""
        if is_workflow_step:
            processed_title = f"Step {order + 1}: {processed_title}"
        endpoint = EndpointDetails(
            rule=f"/{self.name}" + rule,
            task_schema_rule=f"/{self.name}" + rule + "/task_schema",
            func=ml_function,
            task_schema_func=task_schema_func,
            short_title=processed_title,
            order=order,
            help=help,
        )
        self.endpoints.append(endpoint)
        type_hints = get_type_hints(ml_function)
        input_type = type_hints["inputs"]
        parameter_type = type_hints.get("parameters", None)
        if parameter_type and not parameters_cli_parser:
            raise ValueError(
                "parameters_cli_parser is required when parameters are used in the function signature."
            )

        @self.app.command(endpoint.task_schema_rule)
        def get_task_schema():
            res = endpoint.task_schema_func().model_dump(mode="json")
            logger.info(res)
            return res

        logger.debug(f"Registered task schema command: {endpoint.task_schema_rule}")

        if parameter_type:

            @self.app.command(f"/{self.name}" + rule, help=help)
            def run(
                inputs: Annotated[
                    input_type,
                    inputs_cli_parser,
                    Body(embed=True),
                ],
                parameters: Annotated[
                    parameter_type,
                    parameters_cli_parser,
                    Body(embed=True),
                ],
            ):
                if is_async:
                    # For async tasks, explicitly use the pickle serializer to ensure
                    # complex objects (like Pydantic models) are passed correctly to the worker.
                    task = ml_function.apply_async(
                        args=[inputs, parameters], serializer="pickle"
                    )
                    return ResponseBody(root=TextResponse(value=task.id, title="task_id"))

                res = ml_function(inputs, parameters)
                logger.info(res)
                return res

        else:

            @self.app.command(f"/{self.name}" + rule, help=help)
            def run(
                inputs: Annotated[
                    input_type,
                    inputs_cli_parser,
                    Body(embed=True),
                ],
            ):
                if is_async:
                    # For async tasks, explicitly use the pickle serializer to ensure
                    # complex objects (like Pydantic models) are passed correctly to the worker.
                    task = ml_function.apply_async(args=[inputs], serializer="pickle")
                    return ResponseBody(root=TextResponse(value=task.id, title="task_id"))

                res = ml_function(inputs)
                logger.info(res)
                return res
            
        logger.debug(f"Registered ML service command: {rule}")

        # If the service is asynchronous, create a second endpoint to poll for the task result.
        # this is a GET call that has to be allowed in cli.py is_get_request()
        if is_async:
            result_rule = f"/{self.name}{rule}/result/{{task_id}}"

            @self.app.command(result_rule, help="Get the result of an async task.")
            def get_result(task_id: str):
                """Polls for the result of a background task given its ID."""
                result = AsyncResult(task_id, app=rb_celery_app)
                if result.ready():
                    if result.successful():
                        # Task finished successfully, return the actual result.
                        return result.get()
                    else:
                        # Task failed, return the error information.
                        return ResponseBody(
                            root=TextResponse(
                                value=f"Task failed: {result.info}", title="error"
                            )
                        )
                else:
                    # Task is still pending, return its current state.
                    return ResponseBody(
                        root=TextResponse(
                            value=f"Task status: {result.state}", title="status"
                        )
                    )
            logger.debug(f"Registered async result command: {result_rule}")
