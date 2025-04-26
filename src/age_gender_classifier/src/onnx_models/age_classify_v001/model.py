import onnxruntime as ort
import os
import numpy as np
import cv2 as cv
from PIL import Image
from src.utils.preprocess import enhance_image

# Preprocessing function
def preprocess_image(image_input, target_size=224):
    """
    Preprocess either:
      - image_input as an image path(string) to a .jpg/.png file
      - image_input as a 48*48 pixel string
      - image_input as a 48*48 numpy array 
    """
    if isinstance(image_input, str):
        if os.path.exists(image_input):
            image = Image.open(image_input).convert("L") # convert to grayscale
            image = image.resize((48,48))
            image_np = np.array(image, dtype = np.uint8)
        elif image_input.count(" ") >= 2303:
            pixel_vals = np.array([int(p) for p in image_input.strip().split()], dtype=np.uint8)
            image_np = pixel_vals.reshape(48,48)
        else:
            raise ValueError("Invalid string input: not a valid image file or input string")
    elif isinstance(image_input, np.ndarray):
        image_np = image_input
    else:
        raise ValueError("Unsupported input type.")
    # enhance the image
    enhanced = enhance_image(image_np)
    #resized to model input size
    resized = cv.resize(enhanced, (target_size, target_size))
    # convert to float, normalize, and reshape
    final = resized.astype(np.float32) / 255.0
    final = np.stack([final]*3, axis = 0)
    final = np.expand_dims(final, axis=0)
    return final

# Postprocessing function
def postprocess_output(logits):
    """
    Apply softmax to the raw logits and return predicted classes for the batch.
    """
    exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    probabilities = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
    predicted_classes = np.argmax(probabilities, axis=1)
    return predicted_classes, probabilities

# Mapping from classification ids to age ranges (updated based on model's id2label)
id2label = {
    0: "0-2",
    1: "10-19",
    2: "20-29",
    3: "3-9",
    4: "30-39",
    5: "40-49",
    6: "50-59",
    7: "60-69",
    8: "70-79",
}

# Run inference
def predict(image_input, onnx_path):
    # Load ONNX model
    session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    input_tensor = preprocess_image(image_input)
    outputs = session.run(["logits"], {"pixel_values": input_tensor})[0]
    predicted_classes, probabilities = postprocess_output(outputs)
    predicted_class = predicted_classes[0]
    predicted_label = id2label.get(predicted_class, "Unknown")
    confidence = probabilities[0][predicted_class]
    return predicted_label, confidence