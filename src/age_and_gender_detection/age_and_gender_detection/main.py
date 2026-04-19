import os
import logging
import json
import typer
import onnxruntime
from pathlib import Path
from typing import List, TypedDict

from pydantic import DirectoryPath

from rb.lib.ml_service import MLService
from rb.api.models import (
    BatchFileResponse,
    FileFilterDirectory,
    FileResponse,
    InputSchema,
    InputType,
    ResponseBody,
    TaskSchema,
    TextResponse,
)
from age_and_gender_detection.model import AgeGenderDetector


APP_NAME = "age-gender"

# Raster image types expected under ``image_directory`` (validated via ``FileFilterDirectory``).
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif"}


class AgeGenderImageDirectory(FileFilterDirectory):
    """Directory must exist, be non-empty, and contain at least one allowed image extension."""

    path: DirectoryPath
    file_extensions: List[str] = list(IMAGE_EXTENSIONS)

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
    image_directory: AgeGenderImageDirectory


class Parameters(TypedDict):
    pass


server = MLService(APP_NAME)

script_dir = os.path.dirname(os.path.abspath(__file__))
info_file_path = os.path.join(script_dir, "app-info.md")
with open(info_file_path, "r") as f:
    info = f.read()

server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Age and Gender",
    author="UMass RescueLab",
    version="3.0.0",
    info=info,
    gpu=True,
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

    predictions_by_image = model.predict_age_and_gender_on_dir(input_path)
    logger.info(f"Response: {predictions_by_image}")

    file_responses: list[FileResponse] = []
    for image_path, predictions in predictions_by_image.items():
        if not predictions:
            continue

        for i, pred in enumerate(predictions):
            face_num = i + 1
            image_basename = Path(image_path).name
            
            metadata = {
                "Image Path": image_path,
                "Gender": pred["gender"],
                "Age": pred["age"],
                "Bounding Box": str(pred["box"]),
                #"Face Number": face_num,
            }

            file_responses.append(
                FileResponse(
                    file_type="img",
                    path=image_path,
                    title=f"Face {face_num} in {image_basename}",
                    metadata=metadata,
                )
            )

    if not file_responses:
        return ResponseBody(root=TextResponse(value="No faces detected in any images."))

    return ResponseBody(root=BatchFileResponse(files=file_responses))
 


def cli_parser(path: str):
    try:
        logger.debug("Parsing CLI input path: %s", path)
        p = Path(path)
        if not p.exists():
            raise ValueError(f"Directory {p} does not exist.")
        if not p.is_dir():
            raise ValueError(f"Path {p} is not a directory.")
        return Inputs(image_directory=AgeGenderImageDirectory(path=p))
    except Exception as e:
        logger.error("Error parsing CLI input: %s", e)
        raise typer.Abort() from e


server.add_ml_service(
    rule="/predict",
    ml_function=predict,
    inputs_cli_parser=typer.Argument(parser=cli_parser, help="Image directory path"),
    short_title="Age and Gender",
    order=0,
    task_schema_func=task_schema,
)

app = server.app
if __name__ == "__main__":
    app()
