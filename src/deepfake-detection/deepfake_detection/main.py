# imports
import csv
import warnings
import typer
from typing import Any, Dict, List, TypedDict
from pathlib import Path
from rb.lib.ml_service import MLService
from rb.api.models import (
    DirectoryInput,
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
from collections import defaultdict
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")
APP_NAME = "deepfake_detection"

print("start")


# Configure UI Elements in RescueBox Desktop
def create_transform_case_task_schema() -> TaskSchema:
    print("create_transform_case_task_schema called")
    input_schema = InputSchema(
        key="input_dataset",
        label="Path to the directory containing all images",
        input_type=InputType.DIRECTORY,
    )
    output_schema = InputSchema(
        key="output_file",
        label="Path to the output file",
        input_type=InputType.DIRECTORY,
    )
    facecrop_schema = ParameterSchema(
        key="facecrop",
        label="Enable face cropping? (true/false)",
        # input_type=InputType.TEXT,
        value=EnumParameterDescriptor(
            parameter_type=ParameterType.ENUM,
            enum_vals=[
                EnumVal(key="true", label="true"),
                EnumVal(key="false", label="false"),
            ],
            default="false",
            message_when_empty="Select if you want facecropping. Default is false.",
        ),
        # value=TextParameterDescriptor(default="false"),
    )

    return TaskSchema(
        inputs=[input_schema, output_schema],
        parameters=[facecrop_schema],
    )


# Specify the input and output types for the task
class Inputs(TypedDict):
    input_dataset: DirectoryInput
    output_file: DirectoryInput


class Parameters(TypedDict):
    facecrop: str


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

            # Append the result to the list
            model_results.append(processed_prediction)

        results.append(model_results)
    return results


def cli_parser(input: str) -> Inputs:
    print("cli_parser called")
    input_dataset, output_file = input.split(",")
    input_dataset = Path(input_dataset)
    output_file = Path(output_file)

    # Ensure input dataset exists
    if not input_dataset.exists():
        raise ValueError("Input dataset directory does not exist.")

    # Treat output_file as a directory if it doesn't have a file extension
    if output_file.suffix == "":
        output_dir = output_file
    else:
        output_dir = output_file.parent

    # Ensure the output directory exists
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Input dataset: {input_dataset}")
    print(f"Output directory: {output_dir}")
    return {
        "input_dataset": DirectoryInput(path=str(input_dataset)),
        "output_file": DirectoryInput(path=str(output_dir)),
    }


def param_parser(facecrop: str = "false") -> Parameters:
    print("param_parser called")
    return {
        "facecrop": facecrop,
    }


# @server.route(
#     "/predict",
#     task_schema_func=create_transform_case_task_schema,
#     short_title="DeepFake Detection",
#     order=0,
# )
def give_prediction(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    print("give_prediction called")
    input_path = inputs["input_dataset"].path
    out = Path(inputs["output_file"].path)
    selected_models = "BNext_M_ModelONNX,"
    selected_models = selected_models.split(",")

    logger.info(f"Input path: {input_path}")
    logger.info(f"Output path: {out}")
    logger.info(f"Parameters: {parameters}")
    logger.info(f"Selected models: {selected_models}")

    # Filter models
    model_map = {
        "BNext_M_ModelONNX": BNext_M_ModelONNX,
    }
    active_models = [model_map[m]() for m in selected_models if m in model_map]
    logger.info(f"Active models: {[m.__class__.__name__ for m in active_models]}")
    # Need logic to verify that the random num is not already in the directory *******
    out.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    out = out / f"predictions_{now}.csv"

    # Initialize face cropper if requested
    facecropper = None
    facecrop_param = parameters.get("facecrop", "false").lower()
    if facecrop_param in ("true", "1", "yes"):  # enable face cropping
        try:
            model_dir = Path(__file__).resolve().parent / "onnx_models"
            facecropper = ort.InferenceSession(
                str(model_dir / "face_detector.onnx"),
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
        except Exception as e:
            logger.warning(f"Error loading face detector: {e}")
    dataset = defaultDataset(dataset_path=input_path, resolution=224)
    res_list = run_models(active_models, dataset, facecrop=facecropper)
    logger.debug(f"Results list: {res_list}")
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
            path_basename = os.path.basename(full_image_path)
            row_metadata["Image Path"] = full_image_path

            for m_idx, m in enumerate(model_data):
                pred = m["predictions"][i]["prediction"]
                conf = m["predictions"][i]["confidence"]
                model_name = m["name"]
                row_metadata[f"Prediction"] = pred
                row_metadata[f"Confidence"] = f"{conf * 100:.0f}%"
            
            file_responses.append(
                FileResponse(
                    file_type="img",
                    path=full_image_path,
                    title=f"Prediction for {path_basename}",
                    metadata=row_metadata
                )
            )
    if not file_responses:
        return ResponseBody(root=TextResponse(value="No predictions generated or no images found."))
    
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
    name="Image DeepFake Detector",
    author="UMass Rescue",
    version="2.1.0",
    info=app_info,
    plugin_name=APP_NAME,
    gpu=True,
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
