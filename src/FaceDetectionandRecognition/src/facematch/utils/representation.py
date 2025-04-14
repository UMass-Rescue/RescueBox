# built-in dependencies
from typing import Any, Dict, List, Union

# 3rd party dependencies
import numpy as np
import cv2
import onnxruntime as ort

# project dependencies
from deepface.modules import detection
from src.facematch.utils.logger import log_info
from src.facematch.utils import preprocessing

def represent(
    img_path: Union[str, np.ndarray],
    model_name: str = "VGG-Face",
    enforce_detection: bool = True,
    detector_backend: str = "opencv",
    align: bool = True,
    expand_percentage: int = 0,
    normalization: str = "base",
) -> List[Dict[str, Any]]:
    """
    Represent facial images as multi-dimensional vector embeddings.

    Args:
        img_path (str or np.ndarray): The exact path to the image, a numpy array in BGR format,
            or a base64 encoded image. If the source image contains multiple faces, the result will
            include information for each detected face.

        model_name (str): Model for face recognition. Options: VGG-Face, Facenet, Facenet512,
            OpenFace, DeepFace, DeepID, Dlib, ArcFace, SFace and GhostFaceNet

        enforce_detection (boolean): If no face is detected in an image, raise an exception.
            Default is True. Set to False to avoid the exception for low-resolution images.

        detector_backend (string): face detector backend. Options: 'opencv', 'retinaface',
            'mtcnn', 'ssd', 'dlib', 'mediapipe', 'yolov8'.

        align (boolean): Perform alignment based on the eye positions.

        expand_percentage (int): expand detected facial area with a percentage (default is 0).

        normalization (string): Normalize the input image before feeding it to the model.
            Default is base. Options: base, raw, Facenet, Facenet2018, VGGFace, VGGFace2, ArcFace

    Returns:
        results (List[Dict[str, Any]]): A list of dictionaries, each containing the
            following fields:

        - embedding (List[float]): Multidimensional vector representing facial features.
            The number of dimensions varies based on the reference model
            (e.g., FaceNet returns 128 dimensions, VGG-Face returns 4096 dimensions).
        - facial_area (dict): Detected facial area by face detection in dictionary format.
            Contains 'x' and 'y' as the left-corner point, and 'w' and 'h'
            as the width and height. If `detector_backend` is set to 'skip', it represents
            the full image area and is nonsensical.
        - face_confidence (float): Confidence score of face detection. If `detector_backend` is set
            to 'skip', the confidence will be 0 and is nonsensical.
    """
    resp_objs = []

    # model: FacialRecognition = modeling.build_model(model_name)
    onnx_model_path = ""
    ort_session = None
    if model_name == "ArcFace":
        onnx_model_path = "arcface_model.onnx"
    elif model_name == "Facenet512":
        onnx_model_path = "facenet512_model.onnx"
    elif model_name == "GhostFaceNet":
        onnx_model_path = "ghostfacenet_v1.onnx"
    if onnx_model_path != "":
        ort_session = ort.InferenceSession(onnx_model_path)
    model = None
    if model_name == "SFace":
        try:
            weight_file = "face_recognition_sface_2021dec.onnx"
            model = cv2.FaceRecognizerSF.create(
                model=weight_file, config="", backend_id=0, target_id=0
            )
            log_info("SFace model loaded successfully!")
        except Exception as err:
            log_info(f"Exception while calling opencv.FaceRecognizerSF module: {str(err)}")
            raise ValueError(
                "Exception while calling opencv.FaceRecognizerSF module."
                + "This is an optional dependency."
                + "You can install it as pip install opencv-contrib-python."
            ) from err

    # ---------------------------------
    # we have run pre-process in verification. so, this can be skipped if it is coming from verify.
    # target_size = model.input_shape
    target_size = (112, 112)
    if model_name != "SFace":
        target_size = ort_session.get_inputs()[0].shape[1:3]
    log_info(f"target_size: {target_size}")
    if detector_backend != "skip":
        img_objs = detection.extract_faces(
            img_path=img_path,
            target_size=(target_size[1], target_size[0]),
            detector_backend=detector_backend,
            grayscale=False,
            enforce_detection=enforce_detection,
            align=align,
            expand_percentage=expand_percentage,
        )
    else:  # skip
        # Try load. If load error, will raise exception internal
        img, _ = preprocessing.load_image(img_path)
        # --------------------------------
        if len(img.shape) == 4:
            img = img[0]  # e.g. (1, 224, 224, 3) to (224, 224, 3)
        if len(img.shape) == 3:
            img = cv2.resize(img, target_size)
            img = np.expand_dims(img, axis=0)
            # when called from verify, this is already normalized. But needed when user given.
            if img.max() > 1:
                img = (img.astype(np.float32) / 255.0).astype(np.float32)
        # --------------------------------
        # make dummy region and confidence to keep compatibility with `extract_faces`
        img_objs = [
            {
                "face": img,
                "facial_area": {"x": 0, "y": 0, "w": img.shape[1], "h": img.shape[2]},
                "confidence": 0,
            }
        ]
    # ---------------------------------

    for img_obj in img_objs:
        img = img_obj["face"]
        region = img_obj["facial_area"]
        confidence = img_obj["confidence"]
        # custom normalization
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
                embedding = embeddings[0].tolist()
                # embedding = embeddings[0].reshape(-1)
                log_info(f"Embedding type: {type(embedding)}")
            except Exception as e:
                log_info(f"Failed to run inference: {str(e)}")
        else: # Facenet512, ArcFace, GhostFaceNet
            input_name = ort_session.get_inputs()[0].name
            try:
                result = ort_session.run(None, {input_name: img})
            except Exception as e:
                log_info(f"Failed to run inference: {str(e)}")
            # log_info(f"Result: {result[0]}")
            embedding = result[0].flatten()
            log_info(f"Embedding shape: {embedding.shape}")
            # log_info(f"Embedding type: {type(embedding)}")

        resp_obj = {}
        resp_obj["embedding"] = embedding
        resp_obj["facial_area"] = region
        resp_obj["face_confidence"] = confidence
        resp_objs.append(resp_obj)

    return resp_objs

