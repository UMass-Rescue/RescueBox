# built-in dependencies
import os

# 3rd party dependencies
import numpy as np
import cv2
import onnxruntime as ort

# project dependencies
from face_detection_recognition.utils.logger import log_info
from face_detection_recognition.utils import preprocessing


def get_embedding(
    face_img,
    model_name,
    normalization: str = "base",
):
    """Extract embedding using ArcFace ONNX model with NHWC format"""
    onnx_model_path = ""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    models_dir = os.path.join(parent_dir, "models")
    ort_session = None
    if model_name == "ArcFace":
        onnx_model_path = os.path.join(models_dir, "arcface_model_new.onnx")
    elif model_name == "Facenet512":
        onnx_model_path = os.path.join(models_dir, "facenet512_model.onnx")
    elif model_name == "GhostFaceNet":
        onnx_model_path = os.path.join(models_dir, "ghostfacenet_v1.onnx")
    if onnx_model_path != "":
        ort_session = ort.InferenceSession(onnx_model_path)
    model = None
    if model_name == "SFace":
        try:
            weight_file = os.path.join(
                models_dir, "face_recognition_sface_2021dec.onnx"
            )
            model = cv2.FaceRecognizerSF.create(
                model=weight_file, config="", backend_id=0, target_id=0
            )
            log_info("SFace model loaded successfully!")
        except Exception as err:
            log_info(
                f"Exception while calling opencv.FaceRecognizerSF module: {str(err)}"
            )
            raise ValueError(
                "Exception while calling opencv.FaceRecognizerSF module."
                + "This is an optional dependency."
                + "You can install it as pip install opencv-contrib-python."
            ) from err

    target_size = (112, 112)
    if model_name != "SFace":
        target_size = ort_session.get_inputs()[0].shape[1:3]
    log_info(f"target_size: {target_size}")

    # Resize and pad the image to target_size
    if face_img.shape[0] > target_size[0] or face_img.shape[1] > target_size[1]:
        face_img = cv2.resize(face_img, target_size)
    else:
        diff_0 = target_size[0] - face_img.shape[0]
        diff_1 = target_size[1] - face_img.shape[1]
        face_img = np.pad(
            face_img,
            (
                (diff_0 // 2, diff_0 - diff_0 // 2),
                (diff_1 // 2, diff_1 - diff_1 // 2),
                (0, 0),
            ),
            "constant",
        )

    if face_img.shape[0:2] != target_size:
        face_img = cv2.resize(face_img, target_size)

    # normalizing the image pixels
    img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB).astype("float32")
    img = np.expand_dims(img, axis=0)
    img /= 255  # normalize input in [0, 1]

    img = preprocessing.normalize_input(img=img, normalization=normalization)

    # embedding = model.find_embeddings(img)
    embedding = None
    # embedding = model.forward(img)
    if model_name == "SFace":
        try:
            input_blob = (img[0] * 255).astype(np.uint8)

            embeddings = model.feature(input_blob)
            log_info(f"Embedding shape: {embeddings.shape}")
            # log_info(f"Embedding type: {type(embeddings)}")
            # embedding = embeddings[0].tolist()
            embedding = embeddings[0].tolist()
            # embedding = embeddings[0].reshape(-1)
            log_info(f"Embedding type: {type(embedding)}")
        except Exception as e:
            log_info(f"Failed to run inference: {str(e)}")
    else:  # Facenet512, ArcFace, GhostFaceNet
        input_name = ort_session.get_inputs()[0].name
        log_info(f"Input name: {input_name}")
        try:
            result = ort_session.run(None, {input_name: img})
        except Exception as e:
            log_info(f"Failed to run inference: {str(e)}")
        # log_info(f"Result: {result[0][0]}")
        # embedding = result[0].flatten()
        # log_info(f"Embedding shape: {embedding.shape}")
        # log_info(f"Embedding type: {type(embedding)}")
        embedding = result[0][0]
        # log_info(f"Embedding shape: {embedding.shape}")
    embedding_norm = np.linalg.norm(embedding)
    normalized_embedding = embedding / embedding_norm

    return normalized_embedding
