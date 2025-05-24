from typing import TypedDict

from rb.lib.ml_service import MLService
from rb.api.models import (
    InputSchema,
    InputType,
    ParameterSchema,
    EnumParameterDescriptor,
    ResponseBody,
    TaskSchema,
    EnumVal,
    TextResponse,
    DirectoryInput,
)
from text_summary.model import SUPPORTED_MODELS
from text_summary.summarize import process_files
import json
import typer
from pathlib import Path

APP_NAME = "text_summarization"


class Inputs(TypedDict):
    input_dir: DirectoryInput
    output_dir: DirectoryInput


class Parameters(TypedDict):
    model: str


def task_schema() -> TaskSchema:
    input_dir_schema = InputSchema(
        key="input_dir",
        label="Path to the directory containing the input files",
        input_type=InputType.DIRECTORY,
    )
    output_dir_schema = InputSchema(
        key="output_dir",
        label="Path to the directory containing the output files",
        input_type=InputType.DIRECTORY,
    )
    parameter_schema = ParameterSchema(
        key="model",
        label="Model to use for summarization",
        subtitle="Model to use for summarization",
        value=EnumParameterDescriptor(
            enum_vals=[EnumVal(key=model, label=model) for model in SUPPORTED_MODELS],
            default=SUPPORTED_MODELS[0],
        ),
    )
    return TaskSchema(
        inputs=[input_dir_schema, output_dir_schema], parameters=[parameter_schema]
    )


server = MLService(APP_NAME)
server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Text Summarization",
    author="UMass Rescue",
    version="2.0.0",
    info="Summarize text and PDF files in a directory.",
)


def summarize(
    inputs: Inputs,
    parameters: Parameters,
) -> ResponseBody:
    """
    Summarize text and PDF files in a directory.
    """
    input_dir = inputs["input_dir"].path
    output_dir = inputs["output_dir"].path
    model = parameters["model"]

    processed_files = process_files(model, input_dir, output_dir)

    response = TextResponse(value=json.dumps(list(processed_files)))
    return ResponseBody(root=response)


def inputs_cli_parse(input: str) -> Inputs:
    input_dir, output_dir = input.split(",")
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    if not input_dir.exists():
        raise ValueError("Input directory does not exist.")
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    return Inputs(
        input_dir=DirectoryInput(path=input_dir),
        output_dir=DirectoryInput(path=output_dir),
    )


def parameters_cli_parse(model: str) -> Parameters:
    return Parameters(model=model)


server.add_ml_service(
    rule="/summarize",
    ml_function=summarize,
    inputs_cli_parser=typer.Argument(
        parser=inputs_cli_parse, help="Input and output directory paths"
    ),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse, help="Model to use for summarization"
    ),
    short_title="Text Summarization",
    order=0,
    task_schema_func=task_schema,
)

app = server.app
if __name__ == "__main__":
    app()
