from typing import TypedDict
from pathlib import Path
import logging
import json
import typer

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

from .model import SUPPORTED_MODELS
from .process import process_images

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_NAME = "image_summary"


class Inputs(TypedDict):
    input_dir: DirectoryInput
    output_dir: DirectoryInput


class Parameters(TypedDict):
    model: str


def task_schema() -> TaskSchema:
    input_dir_schema = InputSchema(
        key="input_dir",
        label="Path to the directory containing the input images",
        input_type=InputType.DIRECTORY,
    )
    output_dir_schema = InputSchema(
        key="output_dir",
        label="Path to the directory for the output summaries",
        input_type=InputType.DIRECTORY,
    )
    parameter_schema = ParameterSchema(
        key="model",
        label="Model to use for image description",
        subtitle="Model to use for image description",
        value=EnumParameterDescriptor(
            enum_vals=[
                EnumVal(key=model_id, label=model_info["display_name"])
                for model_id, model_info in SUPPORTED_MODELS.items()
            ],
            default=list(SUPPORTED_MODELS.keys())[0],
        ),
    )
    return TaskSchema(
        inputs=[input_dir_schema, output_dir_schema], parameters=[parameter_schema]
    )


server = MLService(APP_NAME)
server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Image Summary",
    author="UMass Rescue",
    version="1.0.0",
    info=(
        "This plugin lets you generate rich descriptions for every image in a folder. "
        "For each image, it identifies the scene and setting, key objects and their attributes (colors, counts, positions), "
        "people and actions (if present), visible text (quoted verbatim), and notable visual details like lighting and composition. "
        "Input: a directory of images. Output: a matching directory of .txt files (one per image) containing the description."
    ),
)


def summarize_images(
    inputs: Inputs,
    parameters: Parameters,
) -> ResponseBody:
    input_dir = inputs["input_dir"].path
    output_dir = inputs["output_dir"].path
    model = parameters["model"]

    logger.info(
        f"ImageSummary API: received request | model={model} | input_dir={input_dir} | output_dir={output_dir}"
    )
    processed_files = process_images(model, input_dir, output_dir)

    response = TextResponse(value=json.dumps(list(processed_files)))
    logger.info(f"ImageSummary API: response ready | files={len(processed_files)}")
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
    rule="/summarize-images",
    ml_function=summarize_images,
    inputs_cli_parser=typer.Argument(
        parser=inputs_cli_parse, help="Input and output directory paths"
    ),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse, help="Model to use for description"
    ),
    short_title="Describe Images",
    order=0,
    task_schema_func=task_schema,
)

app = server.app

if __name__ == "__main__":
    app()
