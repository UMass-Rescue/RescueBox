from dataclasses import dataclass
from logging import getLogger
from typing import Any, Callable, List, Optional, get_type_hints, Annotated

from fastapi import Body
import typer

from rb.api.models import (
    APIRoutes,
    ResponseBody,
    SchemaAPIRoute,
    TaskSchema,
    AppMetadata,
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

            @self.app.command(f"/{self.name}" + rule)
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
                res = ml_function(inputs, parameters)
                logger.info(res)
                return res

        else:

            @self.app.command(f"/{self.name}" + rule)
            def run(
                inputs: Annotated[
                    input_type,
                    inputs_cli_parser,
                    Body(embed=True),
                ],
            ):
                res = ml_function(inputs)
                logger.info(res)
                return res

        logger.debug(f"Registered ML service command: {rule}")
