import cv2
import numpy as np
import onnxruntime as ort


def get_arcface_embedding(face_img, model_path):
    """Extract embedding using ArcFace ONNX model with NHWC format"""
    # Resize to 112x112
    if face_img.shape[0] != 112 or face_img.shape[1] != 112:
        face_img = cv2.resize(face_img, (112, 112))

    # Normalize to [0,1]
    face_img = face_img.astype(np.float32)
    face_img = face_img / 255.0

    # Use NHWC format (just add batch dimension)
    img_input = np.expand_dims(face_img, axis=0)

    # Run inference
    session = ort.InferenceSession(model_path)
    input_name = session.get_inputs()[0].name
    output = session.run(None, {input_name: img_input})[0]

    # L2 normalize
    embedding = output[0]
    embedding_norm = np.linalg.norm(embedding)
    normalized_embedding = embedding / embedding_norm

    return normalized_embedding
