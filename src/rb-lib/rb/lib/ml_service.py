from dataclasses import dataclass
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional, get_type_hints, Annotated
from contextlib import nullcontext

from fastapi import Body
import typer
import threading

from rb.api.models import (
    APIRoutes,
    AppMetadata,
    PipelineFileFilterInputMixin,
    ResponseBody,
    SchemaAPIRoute,
    TaskSchema,
)
from rb.lib.utils import (
    ensure_ml_func_hinting_and_task_schemas_are_valid,
    ensure_ml_func_parameters_are_typed_dict,
)


logger = getLogger(__name__)


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


class MLService(object):
    """
    The MLService object is a wrapper class for the app object. It
    provides a decorator for turning a machine learning prediction function
    into a rest api endpoint.
    """

    def __init__(self, name):
        """
        Instantiates the MLService object as a wrapper for the app.
        """
        self.name = name
        self.app = typer.Typer()
        self.endpoints: List[EndpointDetails] = []
        self._app_metadata: Optional[AppMetadata] = None
        self.plugin_name = name
        self._ml_function_locks: Dict[str, Optional[threading.Lock]] = {}  # New line
        self._make_threadsafe: bool = True

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
            logger.info("%s", res)
            return res

        logger.debug("Registered routes command: /api/routes")

        @self.app.command(f"/{self.name}/api/app_metadata")
        def get_app_metadata():
            if self._app_metadata is None:
                return {"error": "App metadata not set"}
            res = self._app_metadata.model_dump(mode="json")
            logger.info("%s", res)
            return res

    def add_app_metadata(
        self,
        name: str,
        author: str,
        version: str,
        info: str,
        plugin_name: str,
        gpu: bool = False,
        make_threadsafe: bool = True,
    ):
        self._app_metadata = AppMetadata(
            name=name,
            author=author,
            version=version,
            info=info,
            plugin_name=plugin_name,
            gpu=gpu,
            make_threadsafe=make_threadsafe,
        )
        self._make_threadsafe = make_threadsafe

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
    ):
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
        )
        self.endpoints.append(endpoint)

        if self._make_threadsafe:
            self._ml_function_locks[endpoint.rule] = threading.Lock()
        else:
            self._ml_function_locks[endpoint.rule] = None

        type_hints = get_type_hints(ml_function)
        input_type = type_hints["inputs"]
        input_field_hints = get_type_hints(input_type)
        if "file_filter" in input_field_hints:
            merged_inputs_type = input_type
        else:

            class MergedInputs(input_type, PipelineFileFilterInputMixin):
                """Plugin Inputs plus optional pipeline keys (e.g. file_filter) for HTTP bodies."""

            merged_inputs_type = MergedInputs

        parameter_type = type_hints.get("parameters", None)
        if parameter_type and not parameters_cli_parser:
            raise ValueError(
                "parameters_cli_parser is required when parameters are used in the function signature."
            )

        @self.app.command(endpoint.task_schema_rule)
        def get_task_schema():
            res = (
                endpoint.task_schema_func()
                .with_default_pipeline_inputs()
                .for_public_api()
                .model_dump(mode="json")
            )
            logger.info(res)
            return res

        logger.debug("Registered task schema command: %s", endpoint.task_schema_rule)

        if parameter_type:

            @self.app.command(f"/{self.name}" + rule)
            def run(
                inputs: Annotated[
                    merged_inputs_type,
                    inputs_cli_parser,
                    Body(embed=True),
                ],
                parameters: Annotated[
                    parameter_type,
                    parameters_cli_parser,
                    Body(embed=True),
                ],
            ):
                lock = self._ml_function_locks.get(endpoint.rule)
                ctx = lock if lock else nullcontext()
                with ctx:
                    res = ml_function(inputs, parameters)
                logger.info("%s", res)
                return res

        else:

            @self.app.command(f"/{self.name}" + rule)
            def run(
                inputs: Annotated[
                    merged_inputs_type,
                    inputs_cli_parser,
                    Body(embed=True),
                ],
            ):
                lock = self._ml_function_locks.get(endpoint.rule)
                ctx = lock if lock else nullcontext()
                with ctx:
                    res = ml_function(inputs)
                logger.info("%s", res)
                return res

        logger.debug("Registered ML service command: %s", rule)
