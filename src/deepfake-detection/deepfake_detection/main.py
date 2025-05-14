# imports
import csv
import warnings
import typer
from typing import TypedDict
from pathlib import Path
from rb.lib.ml_service import MLService
from rb.api.models import (
    DirectoryInput,
    FileResponse,
    InputSchema,
    InputType,
    ResponseBody,
    TaskSchema,
    ParameterSchema,
    EnumParameterDescriptor,
    # TextParameterDescriptor,
    EnumVal,
    ParameterType,
)
from deepfake_detection.process.bnext_M import BNext_M_ModelONNX
from deepfake_detection.process.bnext_S import BNext_S_ModelONNX
from deepfake_detection.process.transformer import TransformerModelONNX
from deepfake_detection.process.transformerDima_onnx_process import (
    TransformerModelDimaONNX,
)
from deepfake_detection.process.resnet50 import Resnet50ModelONNX
import onnxruntime as ort
from random import randint
import os
from deepfake_detection.sim_data import defaultDataset
from collections import defaultdict
import logging

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
    models_schema = ParameterSchema(
        key="models",
        label="Select Models",
        subtitle="Select the models to use for prediction. By default, all models are selected.",
        value=EnumParameterDescriptor(
            parameter_type=ParameterType.ENUM,
            enum_vals=[
                EnumVal(key="all", label="all"),
                EnumVal(key="BNext_M_ModelONNX", label="BNext_M_ModelONNX"),
                EnumVal(key="BNext_S_ModelONNX", label="BNext_S_ModelONNX"),
                EnumVal(key="TransformerModelONNX", label="TransformerModelONNX"),
                EnumVal(
                    key="TransformerModelDimaONNX", label="TransformerModelDimaONNX"
                ),
                EnumVal(key="Resnet50ModelONNX", label="Resnet50ModelONNX"),
            ],
            default="all",
            message_when_empty="Select the models to use for prediction, default is all.",
        ),
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
        parameters=[models_schema, facecrop_schema],
    )


# Specify the input and output types for the task
class Inputs(TypedDict):
    input_dataset: DirectoryInput
    output_file: DirectoryInput


class Parameters(TypedDict):
    models: str
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


def param_parser(models: str, facecrop: str = "false") -> Parameters:
    print("param_parser called")
    if models == "all":
        models = "BNext_M_ModelONNX,BNext_S_ModelONNX,TransformerModelONNX,TransformerModelDimaONNX, Resnet50ModelONNX"

    return {
        "models": models,
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
    selected_models = parameters.get("models", "all")
    if selected_models == "all":
        selected_models = "BNext_M_ModelONNX,BNext_S_ModelONNX,TransformerModelONNX,TransformerModelDimaONNX, Resnet50ModelONNX"
    selected_models = selected_models.split(",")

    logger.info(f"Input path: {input_path}")
    logger.info(f"Output path: {out}")
    logger.info(f"Parameters: {parameters}")
    logger.info(f"Selected models: {selected_models}")

    # Filter models
    model_map = {
        "BNext_M_ModelONNX": BNext_M_ModelONNX,
        "BNext_S_ModelONNX": BNext_S_ModelONNX,
        "TransformerModelONNX": TransformerModelONNX,
        "TransformerModelDimaONNX": TransformerModelDimaONNX,
        "Resnet50ModelONNX": Resnet50ModelONNX,
    }
    active_models = [model_map[m]() for m in selected_models if m in model_map]
    logger.info(f"Active models: {[m.__class__.__name__ for m in active_models]}")
    # Need logic to verify that the random num is not already in the directory *******
    out.mkdir(parents=True, exist_ok=True)
    out = out / f"predictions_{randint(0, 999)}.csv"

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
    logger.info(f"Results list: {res_list}")
    # Prepare model data structure
    model_data = []
    for model_results in res_list:
        model_name = model_results[0]["model_name"]
        predictions = model_results[1:]
        model_data.append({"name": model_name, "predictions": predictions})
    # Build CSV content
    csv_rows = []
    # Add model names header
    csv_rows.append(["Model:"] + [m["name"] for m in model_data] + ["Aggregate"])
    # Loop over each image (driven by the first model's predictions)
    num_images = len(model_data[0]["predictions"])
    for i in range(num_images):

        # Extract the common image path (basename)
        path = os.path.basename(model_data[0]["predictions"][i]["image_path"])

        # Get each model's prediction and confidence for image i
        preds = [m["predictions"][i]["prediction"] for m in model_data]
        confs = [m["predictions"][i]["confidence"] for m in model_data]

        # --- Aggregate predictions using a weighted vote ---
        # Sum the confidence scores for each prediction label.
        vote_totals = defaultdict(float)
        for pred, conf in zip(preds, confs):
            vote_totals[pred] += conf

        # Choose the label with the highest total confidence.
        agg_pred = max(vote_totals, key=vote_totals.get)

        # Compute the aggregate confidence as the average confidence
        # of the models that predicted the chosen label.
        relevant_confs = [conf for pred, conf in zip(preds, confs) if pred == agg_pred]
        agg_conf = sum(relevant_confs) / len(relevant_confs) if relevant_confs else 0

        # Format the aggregate confidence as a percentage.
        agg_conf_pct = f"{agg_conf * 100:.0f}%"

        # --- Append the rows for this image ---
        csv_rows.append(["Path:"] + [path] * len(model_data) + [path])
        csv_rows.append(["Prediction:"] + preds + [agg_pred])
        csv_rows.append(
            ["Confidence:"] + [f"{conf * 100:.0f}%" for conf in confs] + [agg_conf_pct]
        )

    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)

    return ResponseBody(FileResponse(path=str(out), file_type="csv"))


# ----------------------------
# Server Setup Below
# ----------------------------

# Create a server instance
server = MLService(APP_NAME)

server.add_app_metadata(
    name="Image DeepFake Detector",
    author="UMass Rescue",
    version="0.2.0",
    info="Detects deepfake images using various models. Supports BNext_M, BNext_S, Transformer, and TransformerDima models.",
    plugin_name=APP_NAME,
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
        help="Comma-separated list of models to use (e.g., 'BNext_M_ModelONNX,TransformerModelONNX').",
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
