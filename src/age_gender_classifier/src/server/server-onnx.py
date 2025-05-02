from typing import TypedDict
from pathlib import Path
import json

from src.onnx_models.survey_models import SurveyModels

from flask_ml.flask_ml_server import MLServer, load_file_as_string
from flask_ml.flask_ml_server.models import (
    DirectoryInput,
    TextResponse,
    InputSchema,
    InputType,
    ResponseBody,
    TaskSchema,
    ParameterSchema,
    IntParameterDescriptor,
)


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


server = MLServer(__name__)

server.add_app_metadata(
    name="Age Classifier",
    author="UMass Rescue",
    version="0.2.0",
    info=load_file_as_string("img-app-info.md"),
)


@server.route("/ageclassifier", task_schema_func=create_transform_case_task_schema)
def sentiment_detection(inputs: Inputs, parameters: Parameters) -> ResponseBody:
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


if __name__ == "__main__":
    server.run(port=5000)
