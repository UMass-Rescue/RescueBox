# imports
import csv
import warnings
import typer
from typing import Any, Dict, List, Optional, TypedDict
from pathlib import Path

from pydantic import DirectoryPath
from rb.lib.ml_service import MLService
from rb.api.models import (
    DirectoryInput,
    FileFilterDirectory,
    FileResponse,
    InputSchema,
    InputType,
    ResponseBody,
    BatchFileResponse,
    TaskSchema,
    ParameterSchema,
    EnumParameterDescriptor,
    EnumVal,
    ParameterType,
    TextResponse,
)
from deepfake_detection.process.bnext_M import BNext_M_ModelONNX

import onnxruntime as ort
import os
from deepfake_detection.sim_data import defaultDataset
import logging
from datetime import datetime
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")
APP_NAME = "deepfake_detection"

# Extensions scanned by ``defaultDataset`` in ``sim_data`` (top-level files only).
DEEPFAKE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


class DeepfakeImageDirectory(FileFilterDirectory):
    """Directory must exist, be non-empty, and contain at least one allowed image extension."""

    path: DirectoryPath
    file_extensions: List[str] = list(DEEPFAKE_IMAGE_EXTENSIONS)


print("start")


def _load_face_detector_session():
    """
    RetinaFace ONNX session used to align crops on the detected face before BNext inference.

    Face-aligned inputs typically match the model's training distribution better than raw
    full frames. This session is always passed into ``run_models(..., facecrop=...)`` when
    the ONNX file loads. The task parameter ``facecrop`` only selects whether result rows
    show the saved crop vs the full image; it does not turn this preprocessing off.
    """
    model_dir = Path(__file__).resolve().parent / "onnx_models"
    available = ort.get_available_providers()
    providers = ["CPUExecutionProvider"]
    if "CUDAExecutionProvider" in available:
        providers.insert(
            0,
            (
                "CUDAExecutionProvider",
                {"device_id": 0, "cudnn_conv_algo_search": "DEFAULT"},
            ),
        )
    if "CoreMLExecutionProvider" in available:
        providers.insert(0, "CoreMLExecutionProvider")
    return ort.InferenceSession(
        str(model_dir / "face_detector.onnx"),
        providers=providers,
    )


# Configure UI Elements in RescueBox Desktop
def create_transform_case_task_schema() -> TaskSchema:
    print("create_transform_case_task_schema called")
    input_schema = InputSchema(
        key="input_dir",
        label="Path to the directory containing all images",
        input_type=InputType.DIRECTORY,
    )
    output_schema = InputSchema(
        key="output_dir",
        label="Path to the output file",
        input_type=InputType.DIRECTORY,
    )
    facecrop_schema = ParameterSchema(
        key="facecrop",
        label="Show cropped face in results (true/false)",
        value=EnumParameterDescriptor(
            parameter_type=ParameterType.ENUM,
            enum_vals=[
                EnumVal(key="true", label="true"),
                EnumVal(key="false", label="false"),
            ],
            default="false",
            message_when_empty="true = preview the aligned face crop; false = preview the full image. Model input is unchanged.",
        ),
    )

    return TaskSchema(
        inputs=[input_schema, output_schema],
        parameters=[facecrop_schema],
    )


# Specify the input and output types for the task
class Inputs(TypedDict):
    input_dir: DeepfakeImageDirectory
    output_dir: DirectoryInput


class Parameters(TypedDict):
    """
    ``facecrop``: if true/yes/1, each result row shows the saved face-crop preview when
    available; if false, the row shows the full source image. Processing always runs with
    the face-detector session (when it loads); this flag does not disable it.
    """

    facecrop: str


def _preview_face_crop_in_results(facecrop: str) -> bool:
    return facecrop.strip().lower() in ("true", "1", "yes")


def run_models(models, dataset, facecrop=None):
    print("run_models called")
    results = []
    for model in models:
        model_results = []
        model_results.append({"model_name": model.__class__.__name__})
        # print("Name:", model.__class__.__name__)
        for i in range(
            len(dataset)
        ):  # This is done one image at a time to avoid memory issues
            sample = dataset[i]
            image = sample["image"]
            image_path = sample["image_path"]

            # Preprocess, predict, postprocess (with optional face crop)
            preprocessed_image = model.preprocess(image, facecrop=facecrop)
            prediction = model.predict(preprocessed_image)
            processed_prediction = model.postprocess(prediction)

            # Add image name to prediction
            processed_prediction["image_path"] = image_path
            crop_pv = getattr(model, "last_crop_preview_path", None)
            if crop_pv:
                processed_prediction["crop_preview_path"] = crop_pv

            # Append the result to the list
            model_results.append(processed_prediction)

        results.append(model_results)
    return results


def cli_parser(input: str) -> Inputs:
    print("cli_parser called")
    input_dir, output_dir = input.split(",")
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # Ensure input dataset exists
    if not input_dir.exists():
        raise ValueError("Input dataset directory does not exist.")

    # Treat output_dir as a directory if it doesn't have a file extension
    if output_dir.suffix == "":
        output_dir = output_dir
    else:
        output_dir = output_dir.parent

    # Ensure the output directory exists
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Input dataset: {input_dir}")
    print(f"Output directory: {output_dir}")
    try:
        return Inputs(
            input_dir=DeepfakeImageDirectory(path=input_dir),
            output_dir=DirectoryInput(path=str(output_dir)),
        )
    except Exception as e:
        logger.error("Error parsing CLI inputs: %s", e)
        raise typer.Abort() from e


def param_parser(facecrop: str = "false") -> Parameters:
    print("param_parser called")
    return {"facecrop": facecrop}


_PREDICT_LOCK = threading.Lock()


# @server.route(
#     "/predict",
#     task_schema_func=create_transform_case_task_schema,
#     short_title="DeepFake Detection",
#     order=0,
# )
def give_prediction(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    print("give_prediction called")
    with _PREDICT_LOCK:
        input_path = inputs["input_dir"].path
        out = Path(inputs["output_dir"].path)
        selected_models = ["BNext_M_ModelONNX"]

        logger.info(f"Input path: {input_path}")
        logger.info(f"Output path: {out}")
        logger.info(f"Parameters: {parameters}")
        preview_crop = _preview_face_crop_in_results(
            parameters.get("facecrop", "false")
        )
        logger.info(
            "Result preview: %s",
            "face crop image" if preview_crop else "full image",
        )
        logger.info(f"Selected models: {selected_models}")

        # Filter models
        model_map = {
            "BNext_M_ModelONNX": BNext_M_ModelONNX,
        }
        active_models = [model_map[m]() for m in selected_models if m in model_map]
        logger.info(f"Active models: {[m.__class__.__name__ for m in active_models]}")
        crop_preview_root = out.parent if out.suffix else out
        crop_preview_root.mkdir(parents=True, exist_ok=True)
        for m in active_models:
            setattr(m, "crop_preview_dir", str(crop_preview_root.resolve()))

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        out = crop_preview_root / f"predictions_{now}.csv"

        # Face-aligned crops improve scores; always load when ONNX is available (``facecrop`` only affects result UI).
        facecropper: Optional[ort.InferenceSession] = None
        try:
            facecropper = _load_face_detector_session()
            logger.info(
                "Face detector loaded; preprocess uses face alignment when a face is found (headshot uses full frame)."
            )
        except Exception as e:
            logger.warning(
                "Face detector unavailable (%s); preprocessing falls back to full images only.",
                e,
            )
        dataset = defaultDataset(dataset_path=input_path, resolution=224)
        res_list = run_models(active_models, dataset, facecrop=facecropper)
        logger.debug(f"Results list: {res_list}")

        # Persist aggregate results beside crop previews (CLI and tests expect predictions_*.csv here).
        csv_fields = ["model_name", "image_path", "prediction", "confidence"]
        with open(out, "w", newline="", encoding="utf-8") as csv_f:
            writer = csv.DictWriter(csv_f, fieldnames=csv_fields, extrasaction="ignore")
            writer.writeheader()
            for model_results in res_list:
                mn = model_results[0]["model_name"]
                for row in model_results[1:]:
                    writer.writerow(
                        {
                            "model_name": mn,
                            "image_path": row.get("image_path", ""),
                            "prediction": row.get("prediction", ""),
                            "confidence": row.get("confidence", ""),
                        }
                    )
        logger.info("Wrote predictions CSV to %s", out)

        # Prepare model data structure
        model_data = []
        for model_results in res_list:
            model_name = model_results[0]["model_name"]
            predictions = model_results[1:]
            model_data.append({"name": model_name, "predictions": predictions})

        file_responses: List[FileResponse] = []
        if model_data and model_data[0]["predictions"]:
            num_images = len(model_data[0]["predictions"])
            for i in range(num_images):
                row_metadata: Dict[str, Any] = {}
                # Use the full image_path instead of just the basename
                full_image_path = model_data[0]["predictions"][i]["image_path"]
                os.path.basename(full_image_path)

                crop_preview_path = model_data[0]["predictions"][i].get(
                    "crop_preview_path"
                )
                if preview_crop and crop_preview_path:
                    display_path = crop_preview_path
                    title = "Face crop"
                    row_metadata["Image path"] = full_image_path

                elif preview_crop:
                    display_path = full_image_path
                    title = "Full image"
                else:
                    display_path = full_image_path
                    title = "Full image"

                for m_idx, m in enumerate(model_data):
                    pred = m["predictions"][i]["prediction"]
                    conf = m["predictions"][i]["confidence"]
                    model_name = m["name"]
                    row_metadata["Prediction"] = pred
                    row_metadata["Confidence"] = f"{conf * 100:.0f}%"

                file_responses.append(
                    FileResponse(
                        file_type="img",
                        path=display_path,
                        title=title,
                        metadata=row_metadata,
                    )
                )
        if not file_responses:
            return ResponseBody(
                root=TextResponse(value="No predictions generated or no images found.")
            )

        return ResponseBody(root=BatchFileResponse(files=file_responses))


# ----------------------------
# Server Setup Below
# ----------------------------

# Create a server instance
server = MLService(APP_NAME)

info_file_path = Path(__file__).resolve().parent / "img-app-info.md"
with open(info_file_path, "r", encoding="utf-8") as f:
    app_info = f.read()

server.add_app_metadata(
    name="Detect DeepFakes",
    author="UMass RescueLab",
    version="3.0.0",
    info=app_info,
    plugin_name=APP_NAME,
    gpu=True,
    make_threadsafe=True,
)


server.add_ml_service(
    rule="/predict",
    ml_function=give_prediction,
    inputs_cli_parser=typer.Argument(
        parser=cli_parser,
        help="Provide the input dataset directory and output file path.",
    ),
    parameters_cli_parser=typer.Argument(
        parser=param_parser,
        help="Comma-separated list of models to use (e.g., 'BNext_M_ModelONNX').",
    ),
    short_title="DeepFake Detection",
    order=0,
    task_schema_func=create_transform_case_task_schema,
)

app = server.app
if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Run a server.")
    # parser.add_argument(
    #     "--port", type=int, help="Port number to run the server", default=5000
    # )
    # args = parser.parse_args()
    # server.run(port=args.port)
    app()
