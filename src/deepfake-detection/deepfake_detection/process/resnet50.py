from PIL import Image
import onnxruntime as ort
import numpy as np
from pathlib import Path
from deepfake_detection.process.utils import (
    Compose,
    # InterpolationMode,
    # Resize,
    CenterCrop,
    ToImage,
    ToDtype,
    Normalize,
)


# Trained on COCOFake dataset
class Resnet50ModelONNX:
    def __init__(self, model_path="onnx_models/resnet50_fakes.onnx", resolution=224):
        print("Loading Transformer Model ONNX...")
        # Convert model_path to a Path object
        self.model_path = Path(model_path)
        self.session = ort.InferenceSession(
            str(self.model_path),  # Convert Path object to string for onnxruntime
        )
        self.resolution = resolution
        self.valid_extensions = (".jpg", ".jpeg", ".png")

    def apply_transforms(self, image: Image.Image) -> np.ndarray:
        transform = Compose(
            [
                # Resize(
                #     self.resolution + self.resolution // 8,
                #     interpolation=InterpolationMode.BILINEAR,
                # ),
                CenterCrop(self.resolution),
                ToImage(),
                ToDtype(np.float32, scale=True),
                Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
        out = transform(image)
        out = out.transpose(2, 0, 1)
        return out[None, ...]

    def preprocess(self, image):
        return self.apply_transforms(image)

    def decode_prediction(self, confidence):
        confidence = confidence.item()
        if confidence < 0.2:
            label = "likely fake"
        elif confidence < 0.4:
            label = "weakly fake"
        elif confidence < 0.6:
            label = "uncertain"
        elif confidence < 0.8:
            label = "weakly real"
        else:
            label = "likely real"
        return {"prediction": label, "confidence": confidence}

    def postprocess(self, output):
        logit = float(output[0][0])
        prob = 1.0 / (1.0 + np.exp(-logit))
        return self.decode_prediction(prob)

    def predict(self, input):
        output = self.session.run(None, {"input": input})
        return output[0]
