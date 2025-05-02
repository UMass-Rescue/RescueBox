# survey_models.py

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import logging
import pandas as pd
from src.onnx_models.age_classify_v001.model import predict as predict_age_classifier
from src.onnx_models.vit_age_classifier.model import (
    predict as predict_vit_age_classifier,
)
from src.onnx_models.fairface.model import predict as predict_fairface_classifier

from src.utils.common import write_db, read_db

logging.basicConfig(level=logging.INFO)


def label_to_binary(label, threshold):
    """
    Convert the age range label to a binary value based on a threshold.

    Args:
        label (str): Age range label (e.g., "10-19", "20-29", "more than 70").
        threshold (int): The age threshold (e.g., 20 or 30).

    Returns:
        bool: True if the lower bound of the age range is >= threshold, else False.
    """
    if label.lower().startswith("more"):
        # Treat "more than 70" as age 70 for threshold comparisons.
        age_lower = 70
    else:
        try:
            parts = label.split("-")
            age_lower = int(parts[0])
        except Exception:
            age_lower = 0
    return age_lower >= threshold


class SurveyModels:
    def __init__(self):
        self.base_path = Path(__file__).resolve().parent
        self.model1_path = str(self.base_path / "age_classify_v001/v001_model.onnx")
        self.model2_path = str(self.base_path / "vit_age_classifier/vit_model.onnx")
        self.model3_path = str(self.base_path / "fairface/fairface_age.onnx")
        self.now = datetime.now().isoformat()

        # Check if model files exist
        if not os.path.exists(self.model1_path):
            raise FileNotFoundError(f"Model file not found: {self.model1_path}")
        if not os.path.exists(self.model2_path):
            raise FileNotFoundError(f"Model file not found: {self.model2_path}")
        if not os.path.exists(self.model3_path):
            raise FileNotFoundError(f"Model file not found: {self.model3_path}")

    def predict(self, image_path, imgId):
        """
        Run (both, third to be added) age classification models on the input image.

        Args:
            image_path (str): Path to the input image.

        Returns:
            dict: A dictionary containing the predicted label and confidence for each model.
                  e.g., {"age_classify_v001": (label, confidence), "vit_age_classifier": (label, confidence)}
        """
        # Run the first model
        model1_label, model1_confidence = predict_age_classifier(
            image_path, self.model1_path
        )

        # Run the second model
        model2_label, model2_confidence = predict_vit_age_classifier(
            image_path, self.model2_path
        )

        # Run the third model
        model3_label, model3_confidence = predict_fairface_classifier(
            image_path, self.model3_path
        )

        return {
            "model_name": [
                "age_classify_v001",
                "vit_age_classifier",
                "fairface_classifier",
            ],
            "scores": [
                {
                    "label": model1_label,
                    "confidence": str(model1_confidence),
                    "imageId": imgId,
                },
                {
                    "label": model2_label,
                    "confidence": str(model2_confidence),
                    "imageId": imgId,
                },
                {
                    "label": model3_label,
                    "confidence": str(model3_confidence),
                    "imageId": imgId,
                },
            ],
            "created_at": [self.now] * 3,
        }

    def predict_over_under(self, age, image_path, imgId):
        """
        Poll all 3 models and convert their age predictions into a binary over/under classification.
        Use majority vote instead of random selection.

        Returns:
            dict with keys:
                - model_name: ["predict_over_under"]
                - scores: [{
                    "majority_vote": majority_vote (bool),
                    "binanry_results": {
                        model_name: (bool, confidence), ...
                    }
                }]
                - created_at: [timestamp]
        """
        allowed_ages = {3, 10, 20, 30, 40, 50, 60, 70}
        if age not in allowed_ages:
            raise ValueError(
                f"Invalid age threshold: {age}. Allowed values are {sorted(allowed_ages)}."
            )

        pred = self.predict(image_path, imgId)
        binary_results = {}

        # Count votes for each binary outcome
        vote_counts = {True: 0, False: 0}

        for n in range(len(pred["model_name"])):
            model_name = pred["model_name"][n]
            label = pred["scores"][n]["label"]
            conf = pred["scores"][n]["confidence"]
            is_over = label_to_binary(label, age)

            binary_results[model_name] = (is_over, conf)
            vote_counts[is_over] += 1

        # Majority vote for whether the picture is over the threshold
        majority_vote = True if vote_counts[True] >= 2 else False

        return {
            "model_name": ["predict_over_under"],
            "scores": [
                {
                    "majority_vote": majority_vote,
                    "binary_results": binary_results,
                    "imageId": imgId,
                }
            ],
            "created_at": [self.now],
        }

    def _predict_eval_results(self, age: int, image_path: str, imgId) -> dict:
        """
        Run the age prediction models once and return both the raw predictions (individual labels)
        and the binary over/under vote result (using majority vote) for the specified age threshold.

        Args:
            age (int): The age threshold to convert the predictions to binary.
            image_path (str): Path to the input image.
            imgId: An identifier for the image.

        Returns:
            dict: A dictionary with keys:
                - 'raw_predictions': Output of the original predict() method.
                - 'binary_vote': A dictionary with:
                      * 'majority_vote': The overall binary decision (True if at least 2 models are "over").
                      * 'binary_results': A dict mapping each model name to a tuple (is_over, confidence).
                      * 'imageId': The provided image identifier.
                - 'created_at': The timestamp (from self.now).
        """
        # Run predictions only once
        raw_predictions = self.predict(image_path, imgId)

        # Initialize binary conversion and vote counting
        binary_results = {}
        vote_counts = {True: 0, False: 0}

        for i, model_name in enumerate(raw_predictions["model_name"]):
            # Get the raw label and confidence from predictions
            label = raw_predictions["scores"][i]["label"]
            confidence = raw_predictions["scores"][i]["confidence"]
            # Convert to binary using the helper function
            is_over = label_to_binary(label, age)
            binary_results[model_name] = (is_over, confidence)
            vote_counts[is_over] += 1

        # Majority vote for whether the picture is over the threshold
        majority_vote = True if vote_counts[True] >= 2 else False
        # Combine both results into one output dictionary
        return {
            "raw_predictions": raw_predictions,
            "binary_vote": {
                "majority_vote": majority_vote,
                "binary_results": binary_results,
                "imageId": imgId,
            },
            "created_at": raw_predictions["created_at"][0],
        }

    def main_predict_eval(
        self, images: List, age_threshold: int = 40, ids: Optional[List] = None
    ) -> pd.DataFrame:
        """
        Loop over a list of images and, for each, run the combined evaluation (raw predictions plus binary vote)
        in one pass. Returns a DataFrame with one row per image containing columns:
          - imageId
          - raw_predictions (as a JSON string)
          - binary_vote (as a JSON string)
          - created_at timestamp

        This avoids running separate/redundant predict and predict_over_under calls
        """
        ids = list(range(len(images))) if ids is None else ids
        results = []
        for imgId, img in zip(ids, images):
            combined_result = self._predict_eval_results(age_threshold, img, imgId)[
                "raw_predictions"
            ]
            results.append(pd.DataFrame(combined_result))

        df = pd.concat(results, axis=0).reset_index(drop=True)
        df["scores"] = df["scores"].apply(lambda x: json.dumps(x))

        write_db(df, "model_output")
        logging.info(
            f"Successfully completed combined evaluation for {len(images)} images."
        )
        return df

    def main_predict(
        self, images: List, age_threshold: int = 40, ids: Optional[List] = None
    ) -> pd.DataFrame:
        """Loop list of images, for each, run prediction and write results to db."""
        ids = list(range(len(images))) if ids is None else ids
        ct = 0
        df = None
        for id, img in zip(ids, images):
            df1 = pd.DataFrame(self.predict(img, id))
            df2 = pd.DataFrame(self.predict_over_under(age_threshold, img, id))
            dfs = [df1, df2]
            if ct > 0 and isinstance(df, pd.DataFrame):
                dfs = [df] + dfs
            df = pd.concat(dfs, axis=0).reset_index(drop=True)
            ct += 1

        df["scores"] = df["scores"].apply(lambda x: json.dumps(x))
        write_db(df, "model_output")
        logging.info(
            f" Successfully completed {len(df)} predictions for {len(images)} images."
        )
        return df


# Command Line Execution
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python survey_models.py <image_path> <age_threshold>")
        print("Allowed age thresholds: 3, 10, 20, 30, 40, 50, 60, 70")
        sys.exit(1)

    image_path = sys.argv[1]

    try:
        age_threshold = int(sys.argv[2])
    except ValueError:
        print("Error: Age threshold must be an integer.")
        sys.exit(1)

    allowed_ages = {3, 10, 20, 30, 40, 50, 60, 70}
    if age_threshold not in allowed_ages:
        print(
            f"Error: Invalid age threshold {age_threshold}. Allowed values: {sorted(allowed_ages)}"
        )
        sys.exit(1)

    try:
        survey = SurveyModels()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    # Full Model Predictions
    # predictions = survey.predict(image_path)

    # print("\nModel Predictions:")
    # print(predictions)
    # for x in predictions.items():
    #     print(x)
    # for model_name, (label, confidence) in predictions.items():
    #     print(f"{model_name}: {label} (confidence: {confidence:.2f})")

    # Over/Under Prediction for the specified age
    # binary_result, conf_result = survey.predict_over_under(age_threshold, image_path)
    # chose_model = survey.predict_over_under(age_threshold, image_path)
    # print(chose_model)
    # print(f"\nOver/Under {age_threshold}: {'Over' if binary_result else 'Under'} {age_threshold} (confidence: {conf_result:.2f})")
    df = survey.main_predict([image_path], age_threshold=40)
    df2 = read_db("model_output", "SELECT * FROM model_output")

    # logging.info("Current run", df)
    # logging.info("Read DB", df2.head())
    # python src/onnx_models/survey_models.py src/onnx_models/test_images/lebron.jpg 40
