from PIL import Image
import onnxruntime as ort
import numpy as np
from pathlib import Path
from deepfake_detection.process.utils import (
    Compose,
    InterpolationMode,
    Resize,
    CenterCrop,
    ToImage,
    ToDtype,
)


# Trained on COCOFake dataset
class BNext_M_ModelONNX:
    def __init__(
        self, model_path="onnx_models/bnext_M_dffd_model.onnx", resolution=224
    ):
        print("Loading BNext_M Model ONNX...")
        self.model_path = (
            Path(__file__).resolve().parent.parent
            / "onnx_models"
            / "bnext_M_dffd_model.onnx"
        )
        self.session = ort.InferenceSession(
            str(self.model_path),  # Convert Path object to string for onnxruntime
        )
        self.resolution = resolution
        self.valid_extensions = (".jpg", ".jpeg", ".png")

    def apply_transforms(self, image: Image.Image) -> np.ndarray:
        transform = Compose(
            [
                Resize(
                    self.resolution + self.resolution // 8,
                    interpolation=InterpolationMode.BILINEAR,
                ),
                CenterCrop(self.resolution),
                ToImage(),
                ToDtype(np.float32, scale=True),
            ]
        )
        out = transform(image)  # H×W×C float32 in [0,1]
        out = out.transpose(2, 0, 1)
        return out[None, ...]  # add batch dim

    def preprocess(self, image):
        return self.apply_transforms(image)

    def decode_prediction(self, confidence):

        confidence = confidence.item()

        label = (
            "likely fake"
            if confidence < 0.2
            else (
                "weakly fake"
                if confidence < 0.4
                else (
                    "uncertain"
                    if confidence < 0.6
                    else "weakly real" if confidence < 0.8 else "likely real"
                )
            )
        )

        return {"prediction": label, "confidence": confidence}

    def postprocess(self, output):
        logit = float(output[0][0])
        # numpy sigmoid
        prob = 1.0 / (1.0 + np.exp(-logit))
        return self.decode_prediction(prob)

    def predict(self, input):
        output = self.session.run(None, {"input": input})
        return output[0]
