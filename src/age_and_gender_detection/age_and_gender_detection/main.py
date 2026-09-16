import logging
import os
import threading
from pathlib import Path
from typing import TypedDict

import typer
from pydantic import DirectoryPath
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
from rb.lib.job_progress import report_file_progress
from rb.lib.ml_service import MLService

from age_and_gender_detection.model import AgeGenderDetector, get_images_from_dir

APP_NAME = "age-gender"
server = MLService(APP_NAME)

# Raster image types expected under ``image_directory`` (validated via ``FileFilterDirectory``).
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif"}


class AgeGenderImageDirectory(FileFilterDirectory):
    """Directory must exist, be non-empty, and contain at least one allowed image extension."""

    path: DirectoryPath
    file_extensions: list[str] = list(IMAGE_EXTENSIONS)


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


script_dir = os.path.dirname(os.path.abspath(__file__))
info_file_path = os.path.join(script_dir, "app-info.md")
with open(info_file_path, "r", encoding="utf-8") as f:
    info = f.read()

server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Age and Gender",
    author="UMass RescueLab",
    version="3.0.0",
    info=info,
    gpu=True,
    make_threadsafe=True,
)
models_dir = server.models_dir

model = AgeGenderDetector(
    face_detector_path=models_dir / "version-RFB-640.onnx",
    age_classifier_path=models_dir / "age_googlenet.onnx",
    gender_classifier_path=models_dir / "gender_googlenet.onnx",
)

_PREDICT_LOCK = threading.Lock()


def predict(inputs: Inputs) -> ResponseBody:
    input_path = inputs["image_directory"].path
    logger.info(f"Input path: {input_path}")

    with _PREDICT_LOCK:
        image_files = get_images_from_dir(input_path, model.image_file_extensions)
        total = len(image_files)
        processed = 0
        last_reported = 0
        predictions_by_image: dict[str, list] = {}
        for image_file in image_files:
            try:
                pred = model.predict_age_and_gender(str(image_file))
                predictions_by_image[str(image_file)] = pred
            finally:
                processed += 1
                last_reported = report_file_progress(
                    None, processed, total, last_reported
                )
        if total > 0:
            report_file_progress(None, total, total, last_reported)
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
                # "Face Number": face_num,
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
