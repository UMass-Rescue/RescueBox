import argparse
import onnxruntime as ort
from deepfake_detection.sim_data import defaultDataset
from deepfake_detection.process.transformer import TransformerModelONNX
from deepfake_detection.process.bnext_M import BNext_M_ModelONNX
from deepfake_detection.process.bnext_S import BNext_S_ModelONNX
from deepfake_detection.process.transformerDima_onnx_process import (
    TransformerModelDimaONNX,
)
from deepfake_detection.process.resnet50 import Resnet50ModelONNX
from pathlib import Path
import json
import pandas as pd


def args_func():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset_path",
        type=str,
        required=True,
        help="Path to the dataset folder that contains the test images. The root directory is where this file is located.",
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        required=True,
        help="List of models to use (e.g., TransformerModel BNext_M_ModelONNX). Use 'all' to run all models or 'list' to list available models.",
    )
    parser.add_argument(
        "--facecrop",
        action="store_true",
        help="Enable face cropping before model inference.",
    )

    args = parser.parse_args()
    return args


# Inputs: models (list of model objects), dataset (dataset object)
# Outputs: results (a list of lists of dictionaries, one for each model)
def run_models(models, dataset, facecrop=None):
    results = []
    for model in models:
        print(f"Running model: {model.__class__.__name__}")
        model_results = []
        model_results.append({"model_name": model.__class__.__name__})
        for i in range(
            len(dataset)
        ):  # This is done one image at a time to avoid memory issues
            sample = dataset[i]
            # print(sample)
            image = sample["image"]
            image_path = sample["image_path"]

            # Preprocess the image (with optional face crop)
            preprocessed_image = model.preprocess(image, facecrop=facecrop)

            # Get the prediction
            prediction = model.predict(preprocessed_image)

            # Postprocess the prediction
            processed_prediction = model.postprocess(prediction)

            # Add the name of the image to the prediction
            processed_prediction["image_path"] = image_path

            # Append the result to the list
            model_results.append(processed_prediction)

        results.append(model_results)

    return results


if __name__ == "__main__":
    available_models = {
        cls.__name__: cls
        for cls in [
            BNext_M_ModelONNX,
            BNext_S_ModelONNX,
            TransformerModelONNX,
            TransformerModelDimaONNX,
            Resnet50ModelONNX,
        ]
    }
    input_path = Path("sample_input")

    args = args_func()
    if args.dataset_path:
        input_path = Path(args.dataset_path)
    # Check if the input is a valid path
    if not input_path.exists():
        raise ValueError(f"Invalid path: {input_path}")

    models_to_use = []
    for model in args.models:
        if model == "all":
            models_to_use = [cls() for cls in available_models.values()]
            print("Using all models")
            break
        elif model == "list":
            print("Available models:")
            for model_name in available_models.keys():
                print(model_name)
            exit()
        elif model in available_models:
            models_to_use.append(available_models[model]())
        else:
            # print that model: model is not available
            print(f"Model: {model} is not available")
    if len(models_to_use) == 0:
        raise ValueError(
            "No valid models were selected. Please select at least one model, use 'list' to see available models, or 'all' to use all models."
        )
    else:
        print("Using models:")
        for model in models_to_use:
            print(model.__class__.__name__)
        print("--" * 20)
        print("Using dataset:", input_path)
        print("--" * 20)
        print("Proceed? (y/n)")
        proceed = input().strip().lower()
        if proceed != "y":
            print("Exiting...")
            exit()

    test_dataset = defaultDataset(dataset_path=str(input_path), resolution=224)

    # Initialize face cropper if requested
    facecropper = None
    if args.facecrop:
        try:
            facecropper = ort.InferenceSession(
                str(Path(__file__).parent / "onnx_models/face_detector.onnx"),
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
        except Exception as e:
            print(f"Error loading face detector: {e}")
    results = run_models(models_to_use, test_dataset, facecrop=facecropper)

    output_dir = Path("sample_output")
    output_dir.mkdir(exist_ok=True)  # Create the directory if it doesn't exist
    with open(output_dir / "out.json", "w") as f:
        json.dump(results, f, indent=4)

    flattened_results = [item for model_results in results for item in model_results]
    o = pd.DataFrame(flattened_results)  # Convert to a pandas DataFrame
    o.to_csv(output_dir / "out.csv", index=False)  # Save as a CSV file
