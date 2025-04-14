# built-in dependencies
from typing import Any, Dict, List, Union, Optional, Tuple

# 3rd party dependencies
import numpy as np
import cv2

# project dependencies
from src.facematch.utils import image_utils
from deepface.modules import detection
import onnxruntime as ort
from src.facematch.utils.logger import log_info

from tensorflow.keras.preprocessing import image

def resize_image(img: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    """
    Resize an image to expected size of a ml model with adding black pixels.
    Args:
        img (np.ndarray): pre-loaded image as numpy array
        target_size (tuple): input shape of ml model
    Returns:
        img (np.ndarray): resized input image
    """
    factor_0 = target_size[0] / img.shape[0]
    factor_1 = target_size[1] / img.shape[1]
    factor = min(factor_0, factor_1)

    dsize = (
        int(img.shape[1] * factor),
        int(img.shape[0] * factor),
    )
    img = cv2.resize(img, dsize)

    diff_0 = target_size[0] - img.shape[0]
    diff_1 = target_size[1] - img.shape[1]

    # Put the base image in the middle of the padded image
    img = np.pad(
        img,
        (
            (diff_0 // 2, diff_0 - diff_0 // 2),
            (diff_1 // 2, diff_1 - diff_1 // 2),
            (0, 0),
        ),
        "constant",
    )

    # double check: if target image is not still the same size with target.
    if img.shape[0:2] != target_size:
        img = cv2.resize(img, target_size)

    # make it 4-dimensional how ML models expect
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)

    if img.max() > 1:
        img = (img.astype(np.float32) / 255.0).astype(np.float32)

    return img

def normalize_input(img: np.ndarray, normalization: str = "base") -> np.ndarray:
    """Normalize input image.

    Args:
        img (numpy array): the input image.
        normalization (str, optional): the normalization technique. Defaults to "base",
        for no normalization.

    Returns:
        numpy array: the normalized image.
    """

    # issue 131 declares that some normalization techniques improves the accuracy

    if normalization == "base":
        return img

    # @trevorgribble and @davedgd contributed this feature
    # restore input in scale of [0, 255] because it was normalized in scale of
    # [0, 1] in preprocess_face
    img *= 255

    if normalization == "raw":
        pass  # return just restored pixels

    elif normalization == "Facenet":
        mean, std = img.mean(), img.std()
        img = (img - mean) / std

    elif normalization == "Facenet2018":
        # simply / 127.5 - 1 (similar to facenet 2018 model preprocessing step as @iamrishab posted)
        img /= 127.5
        img -= 1

    elif normalization == "ArcFace":
        # Reference study: The faces are cropped and resized to 112×112,
        # and each pixel (ranged between [0, 255]) in RGB images is normalised
        # by subtracting 127.5 then divided by 128.
        img -= 127.5
        img /= 128
    else:
        raise ValueError(f"unimplemented normalization type - {normalization}")

    return img

def represent(
    img_path: Union[str, np.ndarray],
    model_name: str = "VGG-Face",
    enforce_detection: bool = True,
    detector_backend: str = "opencv",
    align: bool = True,
    expand_percentage: int = 0,
    normalization: str = "base",
    anti_spoofing: bool = False,
    max_faces: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Represent facial images as multi-dimensional vector embeddings.

    Args:
        img_path (str or np.ndarray): The exact path to the image, a numpy array in BGR format,
            or a base64 encoded image. If the source image contains multiple faces, the result will
            include information for each detected face.

        model_name (str): Model for face recognition. Options: Facenet512, ArcFace, SFace and GhostFaceNet

        enforce_detection (boolean): If no face is detected in an image, raise an exception.
            Default is True. Set to False to avoid the exception for low-resolution images.

        detector_backend (string): face detector backend. Options: 'opencv', 'retinaface',
            'mtcnn', 'ssd', 'dlib', 'mediapipe', 'yolov8', 'centerface' or 'skip'.

        align (boolean): Perform alignment based on the eye positions.

        expand_percentage (int): expand detected facial area with a percentage (default is 0).

        normalization (string): Normalize the input image before feeding it to the model.
            Default is base. Options: base, raw, Facenet, Facenet2018, VGGFace, VGGFace2, ArcFace

        anti_spoofing (boolean): Flag to enable anti spoofing (default is False).

        max_faces (int): Set a limit on the number of faces to be processed (default is None).

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

    # model: FacialRecognition = modeling.build_model(
    #     task="facial_recognition", model_name=model_name
    # )
    onnx_model_path = ""
    if model_name == "ArcFace":
        onnx_model_path = "arcface_model.onnx"
    elif model_name == "SFace":
        onnx_model_path = "face_recognition_sface_2021dec.onnx"
    elif model_name == "Facenet512":
        onnx_model_path = "facenet512_model.onnx"
    elif model_name == "GhostFaceNet":
        onnx_model_path = "ghostfacenet_v1.onnx"
    ort_session = ort.InferenceSession(onnx_model_path)

    # ---------------------------------
    # we have run pre-process in verification. so, this can be skipped if it is coming from verify.
    # target_size = model.input_shape
    # log_info(f"target_size: {target_size}" + target_size.shape)
    target_size = ort_session.get_inputs()[0].shape[1:3]
    log_info(f"target_size: {target_size}")

    try:
        if detector_backend != "skip":
            img_objs = detection.extract_faces(
                img_path=img_path,
                detector_backend=detector_backend,
                grayscale=False,
                enforce_detection=enforce_detection,
                align=align,
                expand_percentage=expand_percentage,
                anti_spoofing=anti_spoofing,
            )
        else:  # skip
            # Try load. If load error, will raise exception internal
            img, _ = image_utils.load_image(img_path)
            log_info(f"I was here. img: {img.shape}")
            if len(img.shape) != 3:
                raise ValueError(f"Input img must be 3 dimensional but it is {img.shape}")

            # make dummy region and confidence to keep compatibility with `extract_faces`
            img_objs = [
                {
                    "face": img,
                    "facial_area": {"x": 0, "y": 0, "w": img.shape[0], "h": img.shape[1]},
                    "confidence": 0,
                }
            ]
        # log_info(f"img_objs: {img_objs}")
    except Exception as e:
        log_info(f"Face detection failed {str(e)}")
        raise ValueError(f"Face detection failed {str(e)}")
    # ---------------------------------


    if max_faces is not None and max_faces < len(img_objs):
        # sort as largest facial areas come first
        img_objs = sorted(
            img_objs,
            key=lambda img_obj: img_obj["facial_area"]["w"] * img_obj["facial_area"]["h"],
            reverse=True,
        )
        # discard rest of the items
        img_objs = img_objs[0:max_faces]

    for img_obj in img_objs:
        if anti_spoofing is True and img_obj.get("is_real", True) is False:
            raise ValueError("Spoof detected in the given image.")
        img = img_obj["face"]

        # rgb to bgr
        img = img[:, :, ::-1]

        region = img_obj["facial_area"]
        confidence = img_obj["confidence"]

        try:
            # resize to expected shape of ml model
            img = resize_image(
                img=img,
                # thanks to DeepId (!)
                target_size=(target_size[1], target_size[0]),
            )
            
            # custom normalization
            img = normalize_input(img=img, normalization=normalization)
        except Exception as e:
            log_info(f"Failed to resize or normalize image: {str(e)}")

        # embedding = model.forward(img)
        input_name = ort_session.get_inputs()[0].name
        try:
            result = ort_session.run(None, {input_name: img})
        except Exception as e:
            log_info(f"Failed to run inference: {str(e)}")
        # log_info(f"Result: {result[0]}")
        embedding = result[0].flatten()
        log_info(f"Embedding shape: {embedding.shape}")


        resp_objs.append(
            {
                "embedding": embedding,
                "facial_area": region,
                "face_confidence": confidence,
            }
        )
        # log_info(f"resp_objs: {resp_objs}")
    return resp_objs
