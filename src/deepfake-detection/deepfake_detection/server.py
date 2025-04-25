# imports
import argparse
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
)
from process.bnext_M import BNext_M_ModelONNX
from process.bnext_S import BNext_S_ModelONNX
from process.transformer import TransformerModelONNX
from process.transformerDima_onnx_process import TransformerModelDimaONNX
from random import randint
import os
from sim_data import defaultDataset
from collections import defaultdict

warnings.filterwarnings("ignore")
APP_NAME = "deepfake-detection"

# Configure UI Elements in RescueBox Desktop
def create_transform_case_task_schema() -> TaskSchema:
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
    return TaskSchema(inputs=[input_schema, output_schema], parameters=[])


# Specify the input and output types for the task
class Inputs(TypedDict):
    input_dataset: DirectoryInput
    output_file: DirectoryInput


class Parameters(TypedDict):
    pass


# Create a server instance
server = MLService(APP_NAME)
app = server.app

server.add_app_metadata(
    name="Image DeepFake Detector",
    author="UMass Rescue",
    version="0.2.0",
    info = "Detects deepfake images using various models. Supports BNext_M, BNext_S, Transformer, and TransformerDima models.",
    plugin_name="DEEPFAKE_APP_NAME",
)

models = [
    BNext_M_ModelONNX(),
    BNext_S_ModelONNX(),
    TransformerModelONNX(),
    TransformerModelDimaONNX(),
]


def run_models(models, dataset):
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
            original_res = sample["original_res"]

            # Preprocess, predict, postprocess
            preprocessed_image = model.preprocess(image)
            prediction = model.predict(preprocessed_image)
            processed_prediction = model.postprocess(prediction)

            # Add image name to prediction
            processed_prediction["image_path"] = image_path

            # Append the result to the list
            model_results.append(processed_prediction)

        results.append(model_results)
    return results

def cli_parser(input_dataset, output_file) -> Inputs:
    return {
        "input_dataset": DirectoryInput(path=str(input_dataset)),
        "output_file": DirectoryInput(path=str(output_file)),
    }

def param_parser() -> Parameters:
    return {}

# @server.route(
#     "/predict",
#     task_schema_func=create_transform_case_task_schema,
#     short_title="DeepFake Detection",
#     order=0,
# )
def give_prediction(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    input_path = inputs["input_dataset"].path
    out = Path(inputs["output_file"].path)
    # Need logic to verify that the random num is not already in the directory *******
    random_num = randint(0, 999)
    out = out / (f"predictions_{random_num}.csv")

    dataset = defaultDataset(dataset_path=input_path, resolution=224)

    res_list = run_models(models, dataset)
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

server.add_ml_service(
    rule="/predict",
    ml_function=give_prediction,
    inputs_cli_parser=typer.Argument(parser=cli_parser, help="Input and output directory paths"),
    parameters_cli_parser=typer.Argument(parser=param_parser, help="Model parameters"),
    short_title="DeepFake Detection",
    order=0,
    task_schema_func=create_transform_case_task_schema,
)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Run a server.")
    # parser.add_argument(
    #     "--port", type=int, help="Port number to run the server", default=5000
    # )
    # args = parser.parse_args()
    # server.run(port=args.port)
    app()
