import logging
from typing import TypedDict
import typer
from rb.api.models import (
    InputSchema,
    InputType,
    ResponseBody,
    TaskSchema,
    TextResponse,
    FileInput,
    DirectoryInput,
)
from rb.lib.ml_service import MLService

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

APP_NAME = "hello"
ml_service = MLService(APP_NAME)
ml_service.add_app_metadata(
    plugin_name=APP_NAME,
    name="Hello World",
    author="RescueBox Team",
    version="2.1.0",
    info="A simple Hello World plugin for RescueBox.",
)


class HelloInput(TypedDict):
    input_file: FileInput
    output_dir: DirectoryInput


def task_schema() -> TaskSchema:
    input_schemas = [
        InputSchema(
            key="input_file",
            label="Provide input file",
            input_type=InputType.FILE,
        ),
        InputSchema(
            key="output_dir",
            label="Provide output directory",
            input_type=InputType.DIRECTORY,
        ),
    ]
    return TaskSchema(inputs=input_schemas, parameters=[])


def hello(inputs: HelloInput) -> ResponseBody:
    """Reads a file and writes 'Hello World' to a new file in the output directory."""

    input_file = inputs["input_file"].path
    output_dir = inputs["output_dir"].path

    output_file = output_dir / "output.txt"
    with open(output_file, "w") as f:
        f.write(f"Hello from {input_file.name}")

    result = TextResponse(value=f"Successfully wrote 'Hello World' to {output_file}")
    return ResponseBody(root=result)


def cli_parser(value: str):
    """
    Parses CLI input path and return an object of type HelloInput.
    """
    try:
        input_file, output_dir = value.split(",")
        logger.info("Parsing CLI input path: %s %s", input_file, output_dir)
        inputs = HelloInput(
            input_file=FileInput(path=input_file),
            output_dir=DirectoryInput(path=output_dir),
        )
        return inputs
    except Exception as e:
        logger.error("Error parsing CLI input: %s", e)
        raise typer.Abort()


ml_service.add_ml_service(
    rule="/hello",
    ml_function=hello,
    inputs_cli_parser=typer.Argument(
        parser=cli_parser,
        help="Input file path and output directory path (comma-separated)",
    ),
    task_schema_func=task_schema,
    short_title="Hello World",
    order=0,
)

app = ml_service.app
if __name__ == "__main__":
    app()
