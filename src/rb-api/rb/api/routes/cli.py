import inspect
import json
import logging
import time
from typing import Any, Callable, Generator, Optional

import typer
from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from makefun import with_signature
from pydantic import BaseModel
from rb.api.models import (
    API_APPMETDATA,
    API_ROUTES,
    PLUGIN_SCHEMA_SUFFIX,
    BatchDirectoryResponse,
    BatchFileResponse,
    BatchTextResponse,
    DirectoryResponse,
    FileResponse,
    MarkdownResponse,
    ResponseBody,
    TextResponse,
)
from rb.lib.stdout import Capturing  # type: ignore
from rb.lib.stdout import capture_stdout_as_generator

from rescuebox.main import app as rescuebox_app

logger = logging.getLogger(__name__)

cli_to_api_router = APIRouter()


def static_endpoint(callback: Callable, *args, **kwargs) -> ResponseBody:
    """Execute a CLI command and return the result synchronously"""
    with Capturing() as stdout:
        try:
            logger.debug(
                f"Executing CLI command: {callback.__name__} with args={args}, kwargs={kwargs}"
            )
            result = callback(
                *args, **kwargs
            )  # Ensure this returns a valid Pydantic model

            logger.debug(f"CLI command output type: {type(result)}")

            if isinstance(result, ResponseBody):  # Ensure it's a valid Pydantic model
                return result
            if isinstance(
                result, BaseModel
            ):  # Ensure it's a valid Pydantic model , not sure if this is needed for desktop calls
                return ResponseBody(root=result)
            if isinstance(
                result, dict
            ):  # or Ensure it's a valid dict model for desktop app metadata call to work
                return result
            if isinstance(
                result, list
            ):  # or Ensure it's a valid str model for routes call
                return JSONResponse(content=result)
            if isinstance(
                result, str
            ):  # or Ensure it's a valid str model for routes call
                return ResponseBody(root=TextResponse(value=result))
            # this has an issue of nor sending back details to desktop ui the api caller ?
            raise ValueError(f"Invalid return type from Typer command: {type(result)}")
        except Exception as e:
            # response handler for all plugin runtime errors
            logger.error("Error: %s %s", e, stdout)
            raise HTTPException(  # pylint: disable=raise-missing-from
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": f"{e}"},
            )


def streaming_endpoint(callback: Callable, *args, **kwargs) -> Generator:
    """Execute a CLI command and stream the results with proper response handling"""

    logger.debug(
        f"🚀Streaming started for command: {callback.__name__} with args={args}, kwargs={kwargs}"
    )

    for line in capture_stdout_as_generator(callback, *args, **kwargs):
        try:
            # Attempt to parse the output if it's JSON-like
            parsed_line = (
                json.loads(line)
                if isinstance(line, str) and line.lstrip().startswith("{")
                else line
            )

            response_body = None

            # Dynamically determine the response type
            if isinstance(parsed_line, dict):
                if "texts" in parsed_line:  # Matches BatchTextResponse structure
                    response_body = ResponseBody(root=BatchTextResponse(**parsed_line))
                elif "files" in parsed_line:  # Matches BatchFileResponse structure
                    response_body = ResponseBody(root=BatchFileResponse(**parsed_line))
                elif "directories" in parsed_line:  # Matches BatchDirectoryResponse
                    response_body = ResponseBody(
                        root=BatchDirectoryResponse(**parsed_line)
                    )
                elif "path" in parsed_line:  # Matches FileResponse or DirectoryResponse
                    response_body = ResponseBody(
                        root=(
                            DirectoryResponse(**parsed_line)
                            if parsed_line.get("is_directory")
                            else FileResponse(**parsed_line)
                        )
                    )
                elif "markdown" in parsed_line:  # Matches MarkdownResponse
                    response_body = ResponseBody(root=MarkdownResponse(**parsed_line))
                else:
                    response_body = ResponseBody(
                        root=TextResponse(value=str(parsed_line))
                    )

            elif isinstance(parsed_line, list):
                response_body = ResponseBody(
                    root=BatchTextResponse(
                        texts=[TextResponse(value=str(item)) for item in parsed_line]
                    )
                )

            else:
                # Default to TextResponse if it's a simple string
                response_body = ResponseBody(root=TextResponse(value=str(parsed_line)))

            response_json = response_body.model_dump_json()
            logger.debug(f"Streaming output: {response_json}")
            yield response_json  # Yield properly formatted JSON response

        except Exception as e:
            logger.error(f"Error processing streaming output: {e}")
            yield ResponseBody(
                root=TextResponse(value=f"Error: {str(e)}")
            ).model_dump_json()

        time.sleep(0.01)


def command_callback(command: typer.models.CommandInfo):
    """Create a FastAPI endpoint handler for a Typer CLI command with `ResponseBody`"""

    original_signature = inspect.signature(command.callback)
    new_params = list(original_signature.parameters.values())

    streaming_param = inspect.Parameter(
        "streaming",
        inspect.Parameter.KEYWORD_ONLY,
        default=False,
        annotation=Optional[bool],
    )
    new_params.append(streaming_param)

    new_signature = original_signature.replace(parameters=new_params)

    @with_signature(new_signature)
    def wrapper(*args, **kwargs) -> ResponseBody:
        logger.debug(
            f"FastAPI wrapper called for {command.callback.__name__} with args={args}, kwargs={kwargs}"
        )

        streaming = kwargs.pop("streaming", False)
        if streaming:
            return StreamingResponse(
                streaming_endpoint(command.callback, *args, **kwargs)
            )

        return static_endpoint(command.callback, *args, **kwargs)

    wrapper.__name__ = command.callback.__name__
    wrapper.__doc__ = command.callback.__doc__

    return wrapper


def is_get_request(command: typer.models.CommandInfo) -> bool:
    """Determine if the command should be registered as a GET request"""
    return (
        command.name.endswith(API_APPMETDATA)
        or command.name.endswith(API_ROUTES)
        or command.name.endswith(PLUGIN_SCHEMA_SUFFIX)
    )


for plugin in rescuebox_app.registered_groups:
    router = APIRouter()
    router_with_prefix = APIRouter()
    for command in plugin.typer_instance.registered_commands:
        if command.name:
            logger.debug(f"plugin command name is {command.name}")
            params = {
                "endpoint": command_callback(command),
                "name": command.name,
            }
            if is_get_request(command):
                params["methods"] = ["GET"]
            else:
                params["methods"] = ["POST"]
                params["response_model"] = ResponseBody
            logger.debug(
                f"Registering FastAPI route for {plugin.name} command: {command.name}"
            )
            router.add_api_route(command.name, **params)
        else:
            router_with_prefix.add_api_route(
                f"/{command.callback.__name__}",
                endpoint=command_callback(command),
                methods=["POST"],
                name=command.callback.__name__,
                response_model=Any, # for internal use
            )
            logger.debug(
                f"Registering FastAPI route for {plugin.name} command: {command.callback.__name__}"
            )
    cli_to_api_router.include_router(
        router_with_prefix, prefix=f"/{plugin.name}", tags=[plugin.name]
    )
    cli_to_api_router.include_router(router, tags=[plugin.name])
