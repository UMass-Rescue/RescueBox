"""audio transcribe plugin"""
import sys
import json
import logging
from pathlib import Path
from typing import Annotated, Any, TypedDict
from fastapi import Body, Depends, HTTPException, Response
from rb.api.models import (
    BatchTextResponse,
    DirectoryInput,
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
from rb.api.models import API_APPMETDATA, API_ROUTES, PLUGIN_SCHEMA_SUFFIX
from rb.api.utils import (
    get_int_range_check_func_arg_parser,
    string_to_dict,
)
import typer
from rb_audio_transcription.model import AudioTranscriptionModel
# this here seems to turn on is the log level for the plugin
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = typer.Typer()

model = AudioTranscriptionModel()

info_file_path = Path("app-info.md")


def load_file_as_string(file_path: str) -> str:
    """read in plugin doc"""

    target = Path(__file__).parent.resolve()    
    # pyinstaller exe path
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        temp = getattr(sys, '_MEIPASS', Path(__file__).resolve())
        target = Path(temp) / 'audio'

    full_path = target / Path(file_path)
    
    if not full_path.is_file():
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
    # this is for cli output
    typer.echo(obj)
    # this is for api outpur
    return obj


@app.command(API_ROUTES)  # /api/routes Electron desktop call
def routes() -> Any:
    """return routes"""
    
    route = {
        "task_schema": f'/audio/task{PLUGIN_SCHEMA_SUFFIX}',
        "run_task": "/audio/transcribe",
        "short_title": "audio transcribe",
        "order": 0,
    }
    route_list = [
        route
    ]
    typer.echo(route_list)
    return route_list


# Configure UI Elements in RescueBox Desktop
@app.command(f'task{PLUGIN_SCHEMA_SUFFIX}')
def task_schema() -> Response:
    """return task schema"""
    obj = TaskSchema(
        inputs=[
            InputSchema(
                key="dir_input",
                label="Provide directory with inputs",
                input_type=InputType.DIRECTORY,
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
    typer.echo(obj.model_dump(mode="json"))
    return obj.model_dump(mode="json")


class DirInputs(TypedDict):
    """model input to transcribe"""

    dir_input: DirectoryInput


class FileParameters(TypedDict):
    """model input parameters to transcribe"""

    example_parameter: str
    example_parameter2: float
    example_parameter3: int


def cli_inputs_parser(input_path: str) -> DirInputs:
    '''
    Mandatory cli callback
    input string value to pydantic type
    '''
    try:
        logger.debug("-----DEBUG cli_inputs_parser inputs str to pydantic object ---")
        logger.debug(input_path)
        return DirInputs(
            dir_input=DirectoryInput(path=input_path)
        )
    except Exception as e:
        logger.error(e)
        raise typer.Abort()

def cli_params_parser(p: str) -> FileParameters:
    '''
    Mandatory cli callback
    three parameters of type : string/text , float , int
    '''
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
    # this fucntion is not used , just an example
    try:
        params = string_to_dict(p)
        logger.info("-----DEBUG parser ---")
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

def validate_inputs(inputs: DirInputs):
    '''
    Optional verify inputs are usable callback
    note: fastapi only validates input is a pydantic object
    this fastapi Depends callback checks if files exists in directory
    '''
    try:
        logger.debug("-----validate inputs ---")
        dirpath = inputs["dir_input"].path
        logger.debug("input path %s", dirpath)
        files = [file for file in dirpath.iterdir() if file.is_file()]
        logger.debug(files)
        if len(files) < 1:
            raise HTTPException(status_code=400, detail="no files_in given directory for transcribe command")
        logger.debug("------validate inputs done ---")
        ## this return object is now ready for use in transcribe function
        return inputs
    except (Exception) as e:
        logger.error("validate bad inputs: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid path inputs for transcribe command: {e}")
    
@app.command('transcribe')
def transcribe(
    inputs: Annotated[
        DirInputs,
        typer.Argument(parser=cli_inputs_parser, help="input directory path"),
        Body(embed=True), Depends(validate_inputs)
    ],
    parameters: Annotated[
        FileParameters,
        typer.Argument(parser=cli_params_parser, help="input params range and value "),
        Body(embed=True),
    ] = None,
) -> ResponseBody:
    """Transcribe audio file"""
   
    logger.debug("-----inputs are validated ---")
    logger.debug(parameters)
    dirpath = inputs["dir_input"].path
    logger.debug("-----inputs dir = %s", dirpath)
    logger.debug("------DEBUG ---")

    results = model.transcribe_files_in_directory(dirpath)
    result_texts = [
        TextResponse(value=r["result"], title=r["file_path"]) for r in results
    ]

    logger.info("Transcription Result: %s", result_texts)  # Debug log
    response = BatchTextResponse(texts=result_texts)
    return ResponseBody(root=response)

if __name__ == "__main__":
    app()