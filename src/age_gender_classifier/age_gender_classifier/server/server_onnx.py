from typing import TypedDict
from pathlib import Path
import json
import logging

from age_gender_classifier.onnx_models.survey_models import SurveyModels

from rb.lib.ml_service import MLService
from rb.api.models import (
    DirectoryInput,
    TextResponse,
    InputSchema,
    InputType,
    ResponseBody,
    TaskSchema,
    ParameterSchema,
    IntParameterDescriptor,
)
import typer

logging.basicConfig(level=logging.INFO)


def create_transform_case_task_schema() -> TaskSchema:
    """
    Configure UI Elements in RescueBox Desktop
    InputType.DIRECTORY: a single directory path
    """
    input_schema = InputSchema(
        key="input_dataset",
        label="Path to the directory containing images or videos",
        input_type=InputType.DIRECTORY,
    )
    param_schema = ParameterSchema(
        key="age_threshold",
        label="Age Threshold for Over/Under Prediction",
        value=IntParameterDescriptor(
            default=20,
        ),
    )
    return TaskSchema(inputs=[input_schema], parameters=[param_schema])


class Inputs(TypedDict):
    """Specify the input and output types for the task"""

    input_dataset: DirectoryInput


class Parameters(TypedDict):
    age_threshold: int


APP_NAME = "age-classifier"
server = MLService(APP_NAME)

server.add_app_metadata(
    name=APP_NAME,
    author="UMass Rescue",
    version="0.1.0",
    info="Model to classify ages from images.",
    plugin_name=APP_NAME,
)


def age_classifier(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    """
    In Flask-ML, an inference function takes two arguments: inputs and parameters.
    The types of inputs and parameters must be Python TypedDict types.
    """
    input_path = Path(inputs["input_dataset"].path)
    files = [str(fpath) for fpath in input_path.iterdir() if fpath.is_file()]
    ids = [fpath.stem for fpath in input_path.iterdir() if fpath.is_file()]

    models = SurveyModels()
    df_results = models.main_predict(
        files, age_threshold=parameters["age_threshold"], ids=ids
    )

    return ResponseBody(
        TextResponse(
            value=json.dumps(df_results.T.to_dict(), indent=4),
            title="Output for Age Classifier Models",
        )
    )


def cli_parser(path: str):
    image_directory = path
    try:
        logging.info(f"Parsing CLI input path: {image_directory}")
        image_directory = Path(image_directory)
        if not image_directory.exists():
            raise ValueError(f"Directory {image_directory} does not exist.")
        if not image_directory.is_dir():
            raise ValueError(f"Path {image_directory} is not a directory.")
        inputs = Inputs(input_dataset=DirectoryInput(path=image_directory))
        return inputs
    except Exception as e:
        logging.error(f"Error parsing CLI input: {e}")
        return typer.Abort()


def parameters_cli_parse(age_threshold: str) -> Parameters:
    return Parameters(age_threshold=int(age_threshold))


server.add_ml_service(
    rule="/age_classifier",
    ml_function=age_classifier,
    inputs_cli_parser=typer.Argument(parser=cli_parser, help="Image directory path"),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse, help="Age threshhold"
    ),
    short_title="Age and Gender Classifier",
    order=0,
    task_schema_func=create_transform_case_task_schema,
)


app = server.app
if __name__ == "__main__":
    app()
