from rb.lib.ml_service import MLService
from rb.api.models import (
    DirectoryInput,
    InputSchema,
    InputType,
    TaskSchema,
    ResponseBody,
    TextResponse,
)
from typing import TypedDict
from age_and_gender_detection.model import AgeGenderDetector
from pathlib import Path
import logging
import json
import typer
import onnxruntime

onnxruntime.set_default_logger_severity(3)

APP_NAME = "age-gender"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


# Configure UI Elements in RescueBox Desktop
def task_schema() -> TaskSchema:
    input_schema = InputSchema(
        key="image_directory",
        label="Path to the directory containing all the images",
        input_type=InputType.DIRECTORY,
    )
    return TaskSchema(inputs=[input_schema], parameters=[])


# Specify the input and output types for the task
class Inputs(TypedDict):
    image_directory: DirectoryInput


class Parameters(TypedDict):
    pass


server = MLService(APP_NAME)
server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Age and Gender Classifier",
    author="UMass Rescue",
    version="0.1.0",
    info="Model to classify the age and gender of all faces in an image.",
)
models_dir = Path("src/age_and_gender_detection/models")
model = AgeGenderDetector(
    face_detector_path=models_dir / "version-RFB-640.onnx",
    age_classifier_path=models_dir / "age_googlenet.onnx",
    gender_classifier_path=models_dir / "gender_googlenet.onnx",
)


def predict(inputs: Inputs) -> ResponseBody:
    input_path = inputs["image_directory"].path
    logger.info(f"Input path: {input_path}")
    res_list = model.predict_age_and_gender_on_dir(input_path)
    logger.info(f"Response: {res_list}")
    response = TextResponse(value=json.dumps(res_list))
    return ResponseBody(root=response)


def cli_parser(path: str):
    image_directory = path
    try:
        logger.debug(f"Parsing CLI input path: {image_directory}")
        image_directory = Path(image_directory)
        if not image_directory.exists():
            raise ValueError(f"Directory {image_directory} does not exist.")
        if not image_directory.is_dir():
            raise ValueError(f"Path {image_directory} is not a directory.")
        inputs = Inputs(image_directory=DirectoryInput(path=image_directory))
        return inputs
    except Exception as e:
        logger.error(f"Error parsing CLI input: {e}")
        return typer.Abort()


server.add_ml_service(
    rule="/predict",
    ml_function=predict,
    inputs_cli_parser=typer.Argument(parser=cli_parser, help="Image directory path"),
    short_title="Age and Gender Classifier",
    order=0,
    task_schema_func=task_schema,
)

app = server.app
if __name__ == "__main__":
    app()
