from pathlib import Path
from PIL import Image
import onnxruntime as ort
import numpy as np


class TransformerModelONNX:
    def __init__(
        self, model_path="onnx_models/transformer_model_deepfake.onnx", resolution=224
    ):
        print("Loading Transformer Model ONNX...")
        self.model_path = (
            Path(__file__).resolve().parent.parent
            / "onnx_models"
            / "transformer_model_deepfake.onnx"
        )
        self.session = ort.InferenceSession(
            str(self.model_path),  # Convert Path object to string for onnxruntime
        )
        self.resolution = resolution
        self.valid_extensions = (".jpg", ".jpeg", ".png")

    def apply_transforms(self, image):
        # Resize the image to the required resolution
        image = image.resize(
            (self.resolution, self.resolution)
        )  # , Image.BILINEAR) #Did not use bilinear when making the model onnx.
        # Convert the image to a numpy array
        image = np.array(image).astype(np.float32)
        # Normalize the image
        image = image / 255.0
        # Reorder dimensions to (channels, height, width)
        image = np.transpose(
            image, (2, 0, 1)
        )  # Convert from (height, width, channels) to (channels, height, width)
        # Add a batch dimension
        image = np.expand_dims(image, axis=0)
        return image

    def predict(self, image):
        # Get the prediction
        results = self.session.run(None, {"input": image})
        # Return the results
        # print(results)
        return results[0]

    def preprocess(self, image):
        # We don't preprocess anything for this model
        # Resize the image to the required resolution
        image = self.apply_transforms(image)
        return image

    def preprocess_images(self, images):
        # We don't preprocess anything for this model
        # Resize the images to the required resolution
        for i in range(len(images)):
            images[i] = self.apply_transforms(images[i])
        return images

    def postprocess(self, prediction_result):
        # Process a single prediction result
        # print("r", prediction_result)
        # Check which label has the highest score
        # -- Model automatically has max_score = prediction_result[0]
        # -- If we notice that later a score below 50% is classified as the 'prediction'
        #   replace the below code with this:
        # prediction = prediction_result[0] if max(prediction_result[0]['score'], prediction_result[1]['score']) else prediction_result[1]

        # Apply softmax to normalize the prediction result
        exp_scores = np.exp(prediction_result[0])  # Exponentiate the scores
        probabilities = exp_scores / np.sum(
            exp_scores
        )  # Normalize by dividing by the sum of exponentiated scores
        # Format the prediction result

        confidence = float(max(probabilities))
        raw_label = "real" if probabilities[0] > probabilities[1] else "fake"
        strength = (
            "likely"
            if confidence < 0.2 or confidence > 0.8
            else "weakly" if confidence < 0.4 or confidence > 0.6 else "uncertain"
        )

        if strength == "uncertain":
            label = "uncertain"
        else:
            label = f"{strength} {raw_label}"

        prediction = {"prediction": label, "confidence": confidence}

        # Return the processed result
        return prediction

    def postprocess_images(self, prediction_results):
        # Process all prediction results
        processed_results = []
        for result in prediction_results:
            processed_result = self.postprocess(result)
            processed_results.append(processed_result)
        return processed_results
