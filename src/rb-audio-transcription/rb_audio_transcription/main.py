"""audio transcribe plugin"""

import json
import os
import logging
from pathlib import Path
from typing import Annotated, Any, TypedDict
from fastapi import Body, Depends, HTTPException, Response
from rb.api.models import (
    BatchTextResponse,
    FileInput,
    FloatParameterDescriptor,
    InputSchema,
    InputType,
    IntParameterDescriptor,
    IntRangeDescriptor,
    ParameterSchema,
    RangedIntParameterDescriptor,
    ResponseBody,
    TaskSchema,
    TextParameterDescriptor,
    TextResponse,
)
from rb.api.models import BatchFileInput
from rb.api.models import API_APPMETDATA, API_ROUTES, PLUGIN_SCHEMA_SUFFIX
from rb.api.utils import (
    get_int_range_check_func_arg_parser,
    is_pathname_valid,
    is_pathname_valid_arg_parser,
    string_to_dict,
)
import typer
from .model import AudioTranscriptionModel

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = typer.Typer()

model = AudioTranscriptionModel()

info_file_path = os.path.join("app-info.md")


def load_file_as_string(file_path: str) -> str:
    """read in plugin doc"""

    # Target file or directory
    target = Path(__file__).parent.resolve()
    full_path = os.path.join(target, file_path)

    fp = Path(full_path)
    if not fp.is_file():
        raise FileNotFoundError(f"File {full_path} not found")
    with open(full_path, "r") as f:
        return f.read()


@app.command(API_APPMETDATA)  # ("/api/app_metadata") Electron desktop call
def app_metadata() -> Any:
    """return app_metadata"""
    obj = {
        "name": "Audio Transcription",
        "author": "RescueBox Team",
        "version": "0.1.0",
        "info": load_file_as_string(info_file_path),
    }
    return obj


@app.command(API_ROUTES)  # /api/routes Electron desktop call
def routes() -> Any:
    """return routes"""
    
    route = {
        "task_schema": f'task{PLUGIN_SCHEMA_SUFFIX}',
        "run_task": "/audio/transcribe",
        "payload_schema": "/audio/payload_schema",
        "sample_payload": "/audio/facematch",
        "short_title": "audio transcribe",
        "order": 0,
    }
    route_list = [
        route,
    ]
    logger.info(type(routes))
    return route_list


# Configure UI Elements in RescueBox Desktop
@app.command(f'task{PLUGIN_SCHEMA_SUFFIX}')
def task_schema() -> Response:
    """return task schema"""
    obj = TaskSchema(
        inputs=[
            InputSchema(
                key="file_inputs",
                label="Provide text inputs",
                input_type=InputType.BATCHFILE,
            )
        ],
        parameters=[
            ParameterSchema(
                key="example_parameter",
                label="example_parameter",
                value=TextParameterDescriptor(default="example_value"),
            ),
            ParameterSchema(
                key="example_parameter2",
                label="example_parameter2",
                value=FloatParameterDescriptor(default=0.5),
            ),
            ParameterSchema(
                key="example_parameter3",
                label="example_parameter3",
                value=IntParameterDescriptor(default=5),
            ),
        ],
    )
    return obj.model_dump(mode="json")


class FileInputs(TypedDict):
    """model input to transcribe"""

    file_inputs: BatchFileInput


class FileParameters(TypedDict):
    """model input parameters to transcribe"""

    example_parameter: str
    example_parameter2: float
    example_parameter3: int


def cli_inputs_parser(input_path: str) -> FileInputs:
    """input string value to pydantic type"""
    try:
        logger.debug("-----DEBUG cli_inputs_parser inputs str to pydantic object ---")
        logger.debug(input_path)
        if is_pathname_valid(input_path):
            return FileInputs(
                file_inputs=BatchFileInput(files=[FileInput(path=input_path)])
            )
        raise typer.Abort()
    except Exception as e:
        logger.error("Invalid full path input for transcribe command: %s %s", input_path, e)
        raise typer.Abort()
        #return FileInputs(file_inputs=BatchFileInput(files=[]))


def cli_params_parser(p: str) -> FileParameters:
    """three parameters of type ; string/text , floar , int"""
    try:
        params = string_to_dict(p)
        logger.debug("-----DEBUG FileParameters parser %s ---", params)
        return [
            ParameterSchema(
                key="example_parameter",
                label="string param",
                value=TextParameterDescriptor(default=params["e1"]),
            ),
            ParameterSchema(
                key="example_parameter2",
                label="float param",
                value=FloatParameterDescriptor(default=params["e2"]),
            ),
            ParameterSchema(
                key="example_parameter3",
                label="int param",
                value=IntParameterDescriptor(default=params["e3"]),
            ),
        ]
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error("Invalid parameter input for transcribe: %s", e)
        raise typer.Abort()


def alternate_params_parser(p: str) -> ParameterSchema:
    # range of int values key: str, label: str, minx: int, maxx:int, val:int
    # this fucntion is not used , just to show an example
    try:
        params = string_to_dict(p)
        # logger.info(f"-----DEBUG parser ---")
        range_object = IntRangeDescriptor(min=params["c"], max=params["d"])
        func = get_int_range_check_func_arg_parser(range_object)
        if func(params["e"]):
            return [
                ParameterSchema(
                    key=params["a"],
                    label=params["b"],
                    value=RangedIntParameterDescriptor(
                        range=IntRangeDescriptor(min=params["c"], max=params["d"]),
                        default=params["e"],
                    ),
                )
            ]
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error("Invalid data format: %d", e)
        raise typer.Abort()

def validate_inputs(inputs: FileInputs):
    '''
    verify inputs are usable
    note: fastapi only validates input is a pydantic object
    this fastapi Depends callback checks if path/file exists
    '''
    try:
        logger.debug("-----validate DEBUG inputs ---")
        logger.debug("length input files %d", len(inputs["file_inputs"].files))
        files = [is_pathname_valid_arg_parser(e.path) for e in inputs["file_inputs"].files]
        logger.debug(files)
        if len(files) < 1:
            raise HTTPException(status_code=400, detail=f"no 'file_inputs' for transcribe command")
        logger.debug("------validate DEBUG ---")
        ## this return object is now ready for use in transcribe function
        return inputs
    except (Exception) as e:
        logger.error("validate bad inputs: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid path inputs for transcribe command: {e}")
    
@app.command(f'transcribe')
def transcribe(
    inputs: Annotated[
        FileInputs,
        typer.Argument(parser=cli_inputs_parser, help="input file path"),
        Body(embed=True), Depends(validate_inputs)
    ],
    parameters: Annotated[
        FileParameters,
        typer.Argument(parser=cli_params_parser, help="input params range and value "),
        Body(embed=True),
    ] = None,
) -> ResponseBody:
    """Transcribe audio file"""
   
    logger.debug("-----DEBUG inputs are already validated ---")
    logger.debug(parameters)
    files = [e.path for e in inputs["file_inputs"].files]
    logger.debug(files)
    logger.debug("------DEBUG ---")

    if not files:
        typer.echo("invalid audio file paths given.")
        raise typer.Exit(code=1)

    results = model.transcribe_batch(files)
    result_texts = [
        TextResponse(value=r["result"], title=r["file_path"]) for r in results
    ]

    logger.info("Transcription Result: %s", result_texts)  # Debug log
    response = BatchTextResponse(texts=result_texts)
    return ResponseBody(root=response)
