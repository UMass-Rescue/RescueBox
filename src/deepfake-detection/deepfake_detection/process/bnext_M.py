from PIL import Image
import onnxruntime as ort
import numpy as np
from deepfake_detection.process.facedetector import faceDetector
from pathlib import Path
from deepfake_detection.process.utils import (
    Compose,
    InterpolationMode,
    Resize,
    CenterCrop,
    ToImage,
    ToDtype,
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Trained on COCOFake dataset
class BNext_M_ModelONNX:
    def __init__(
        self, model_path="onnx_models/bnext_M_dffd_model.onnx", resolution=224
    ):
        logger.info("Loading BNext_M Model ONNX...")
        self.model_path = (
            Path(__file__).resolve().parent.parent
            / "onnx_models"
            / "bnext_M_dffd_model.onnx"
        )
        providers = [
            "CUDAExecutionProvider",
            "CPUExecutionProvider",
        ]
        sess_options = ort.SessionOptions()
        self.session = ort.InferenceSession(
            str(self.model_path),  # Convert Path object to string for onnxruntime
            sess_options=sess_options,
            providers=providers,
        )
        dev = ort.get_device()
        logger.info("BNext_M Model ONNX %s", dev)
        # Get input and output memory info
        try:
            available_providers = ort.get_available_providers()
            logger.info("ort available_providers %s", available_providers)
        except Exception as e:
            logger.error(f"Error getting available providers: {e}")

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

    def preprocess(self, image, facecrop=None):
        # Optional face cropping
        if facecrop:
            self.resolution_ratio = getattr(self, "resolution_ratio", 1.5)
            try:
                np_image = np.array(image.convert("RGB"))
                boxes, labels, scores, center, already_headshot = faceDetector(
                    np_image, face_detector=facecrop
                )
            except Exception:
                center, already_headshot = None, False
            if already_headshot:
                return self.apply_transforms(image)
            if center is not None:
                cx, cy = center
                w_img, h_img = image.size
                half = int(self.resolution * self.resolution_ratio / 2)
                left = max(0, cx - half)
                top = max(0, cy - half)
                right = min(w_img, cx + half)
                bottom = min(h_img, cy + half)
                if right > left and bottom > top:
                    image = image.crop((left, top, right, bottom))
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
