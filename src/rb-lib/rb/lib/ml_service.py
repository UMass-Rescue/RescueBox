from dataclasses import dataclass
from logging import getLogger
from typing import Any, Callable, List, Optional, get_type_hints, Annotated

from fastapi import Body, Depends
import typer

from rb.api.models import (
    APIRoutes,
    NoSchemaAPIRoute,
    ResponseBody,
    SchemaAPIRoute,
    TaskSchema,
    AppMetadata,
)
from rb.lib.utils import (
    ensure_ml_func_hinting_and_task_schemas_are_valid,
    ensure_ml_func_parameters_are_typed_dict,
    schema_get_sample_payload,
)

logger = getLogger(__name__)


@dataclass
class EndpointDetailsNoSchema:
    rule: str
    payload_schema_rule: str
    sample_payload_rule: str
    func: Callable[..., ResponseBody]


@dataclass
class EndpointDetails(EndpointDetailsNoSchema):
    task_schema_rule: str
    task_schema_func: Callable[[], TaskSchema]
    short_title: str
    order: int


class MLService(object):
    """
    The MLService object is a wrapper class for the flask app object. It
    provides a decorator for turning a machine learning prediction function
    into a WebService on an applet.
    """

    def __init__(self, name):
        """
        Instantiates the MLService object as a wrapper for the Flask app.
        """
        self.name = name
        self.app = typer.Typer()
        self.endpoints: List[EndpointDetailsNoSchema] = []
        self._app_metadata: Optional[AppMetadata] = None

        @self.app.command(f"/{self.name}/api/routes")
        def list_routes():
            """
            Lists all the routes/endpoints available in the Flask app.
            """
            routes = [
                (
                    SchemaAPIRoute(
                        task_schema=endpoint.task_schema_rule,
                        run_task=endpoint.rule,
                        sample_payload=endpoint.sample_payload_rule,
                        payload_schema=endpoint.payload_schema_rule,
                        short_title=endpoint.short_title,
                        order=endpoint.order,
                    )
                    if isinstance(endpoint, EndpointDetails)
                    else NoSchemaAPIRoute(
                        run_task=endpoint.rule,
                        sample_payload=endpoint.sample_payload_rule,
                        payload_schema=endpoint.payload_schema_rule,
                    )
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

    def add_app_metadata(self, name: str, author: str, version: str, info: str):
        self._app_metadata = AppMetadata(
            name=name, author=author, version=version, info=info
        )

    def add_ml_service(
        self,
        rule: str,
        ml_function: Callable[[Any, Any], ResponseBody],
        inputs_cli_parser,
        parameters_cli_parser,
        task_schema_func: Optional[Callable[[], TaskSchema]] = None,
        short_title: Optional[str] = None,
        order: int = 0,
        validate_inputs=None,
    ):
        ensure_ml_func_parameters_are_typed_dict(ml_function)
        ensure_ml_func_hinting_and_task_schemas_are_valid(
            ml_function, task_schema_func()
        )
        endpoint = EndpointDetails(
            rule=f"/{self.name}" + rule,
            task_schema_rule=f"/{self.name}" + rule + "/task_schema",
            sample_payload_rule=f"/{self.name}" + rule + "/sample_payload",
            payload_schema_rule=f"/{self.name}" + rule + "/payload_schema",
            func=ml_function,
            task_schema_func=task_schema_func,
            short_title=short_title or "",
            order=order,
        )
        self.endpoints.append(endpoint)
        type_hints = get_type_hints(ml_function)
        input_type = type_hints["inputs"]
        parameter_type = type_hints.get("parameters", None)
        validate_inputs = validate_inputs if validate_inputs else lambda x: x

        @self.app.command(f"/{self.name}" + endpoint.task_schema_rule)
        def get_task_schema():
            res = endpoint.task_schema_func().model_dump(mode="json")
            logger.info(res)
            return res

        logger.debug(f"Registered task schema command: {endpoint.task_schema_rule}")

        @self.app.command(f"/{self.name}" + endpoint.sample_payload_rule)
        def get_sample_payload():
            res = schema_get_sample_payload(endpoint.task_schema_func()).model_dump(
                mode="json"
            )
            logger.info(res)
            return res

        logger.debug(
            f"Registered sample payload command: {endpoint.sample_payload_rule}"
        )

        @self.app.command(f"/{self.name}" + endpoint.payload_schema_rule)
        def get_payload_schema():
            res = schema_get_sample_payload(
                endpoint.task_schema_func()
            ).model_json_schema()
            logger.info(res)
            return res

        logger.debug(
            f"Registered payload schema command: {endpoint.payload_schema_rule}"
        )

        @self.app.command(f"/{self.name}" + rule)
        def wrapper(
            inputs: Annotated[
                input_type,
                inputs_cli_parser,
                Body(embed=True),
                Depends(validate_inputs),
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

        logger.debug(f"Registered ML service command: {rule}")
