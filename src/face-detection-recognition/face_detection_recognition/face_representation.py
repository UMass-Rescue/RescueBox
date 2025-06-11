from face_detection_recognition.utils.yolo_utils import (
    get_target_size,
    process_yolov8_output,
    visualize_detections,
    process_yolo_detections,
)

from face_detection_recognition.utils.retinaface_utils import (
    detect_with_retinaface,
    process_retinaface_detections_for_facenet512,
    process_retinaface_detections_for_arcface,
)

import os
import cv2
import numpy as np
import onnxruntime as ort
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def detect_faces_and_get_embeddings(
    image_paths,
    model_name="ArcFace",
    detector_backend="retinaface",
    detector_onnx_path=None,
    face_confidence_threshold=0.02,
    align=True,
    normalization=True,
    input_size=(640, 640),
    visualize=False,
    height_factor=1.5,
    separate_detections=False,  # boolean whether or not to separate detections per img in output,
):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, "models")

    # Set detector path based on backend
    if detector_backend == "yolov8":
        detector_onnx_path = os.path.join(models_dir, "yolov8-face-detection.onnx")
    elif detector_backend == "retinaface":
        detector_onnx_path = os.path.join(models_dir, "retinaface-resnet50.onnx")

    if visualize:
        os.makedirs("debug_detections", exist_ok=True)

    try:
        if detector_onnx_path is None or not os.path.isfile(detector_onnx_path):
            logger.error(f"ONNX model not found: {detector_onnx_path}")
            return False, []

        imgs = []
        original_sizes = []

        target_size = get_target_size(model_name)

        for image_path in image_paths:
            img = cv2.imread(image_path)
            if img is None:
                img_raw = cv2.imread(image_path, cv2.IMREAD_COLOR)
                if img_raw is None:
                    logger.error(f"Failed to load image: {image_path}")
                    img = np.zeros((480, 640, 3), dtype=np.uint8)
                else:
                    img = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)
            else:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            imgs.append(img)

            original_size = (img.shape[1], img.shape[0])
            original_sizes.append(original_size)

        all_boxes, all_scores, all_landmarks = [], [], []
        if detector_backend == "retinaface":
            try:
                for img_rgb, image_path in zip(imgs, image_paths):
                    boxes, scores, landmarks = detect_with_retinaface(
                        image_path=image_path,  # if isinstance(image_path, str) else None,
                        img_rgb=img_rgb,  # if not isinstance(image_path, str) else None,
                        model_path=detector_onnx_path,
                        confidence_threshold=0.02,
                        visualize=visualize,
                    )
                    all_boxes.append(boxes)
                    all_scores.append(scores)
                    all_landmarks.append(landmarks)
                if model_name == "Facenet512":
                    # Facenet512 pipeline
                    face_embeddings = process_retinaface_detections_for_facenet512(
                        imgs,
                        align,
                        target_size,
                        visualize,
                        image_paths,
                        model_name,
                        all_boxes,
                        all_scores,
                        all_landmarks,
                        separate_detections,
                    )
                elif model_name == "ArcFace":
                    # ArcFace-optimized pipeline
                    face_embeddings = process_retinaface_detections_for_arcface(
                        imgs,
                        align,
                        target_size,
                        normalization,
                        visualize,
                        image_paths,
                        model_name,
                        all_boxes,
                        all_scores,
                        all_landmarks,
                        separate_detections,
                    )

                if len(face_embeddings) > 0:
                    return True, face_embeddings
                return False, []

            except Exception as e:
                logger.error(f"Error in RetinaFace: {str(e)}")
                # Fall back to YOLO detector
                detector_backend = "yolov8"
                detector_onnx_path = os.path.join(
                    models_dir, "yolov8-face-detection.onnx"
                )

        # YOLO models processing
        session_options = ort.SessionOptions()
        providers = []
        available_providers = ort.get_available_providers()

        if "CUDAExecutionProvider" in available_providers:
            pvdr = "CUDAExecutionProvider"
            providers.insert(0, pvdr)

        providers.append("CPUExecutionProvider")

        detector_session = ort.InferenceSession(
            detector_onnx_path, sess_options=session_options, providers=providers
        )

        model_inputs = detector_session.get_inputs()
        input_name = model_inputs[0].name

        # YOLO preprocessing
        letterbox_info = None
        if detector_backend == "yolov8":

            all_boxes, all_scores, all_landmarks = [], [], []
            for img, original_size in zip(imgs, original_sizes):

                scale = min(
                    input_size[0] / original_size[0], input_size[1] / original_size[1]
                )
                new_w = int(original_size[0] * scale)
                new_h = int(original_size[1] * scale)
                pad_w = (input_size[0] - new_w) // 2
                pad_h = (input_size[1] - new_h) // 2

                letterbox_info = {
                    "scale": scale,
                    "pad_w": pad_w,
                    "pad_h": pad_h,
                    "orig_size": original_size,
                }

                img_resized = cv2.resize(img, (new_w, new_h))
                letterbox_img = np.zeros(
                    (input_size[1], input_size[0], 3), dtype=np.uint8
                )
                letterbox_img[pad_h : pad_h + new_h, pad_w : pad_w + new_w, :] = (
                    img_resized
                )
                img_norm = letterbox_img.astype(np.float32) / 255.0
                img_input = np.expand_dims(img_norm.transpose(2, 0, 1), axis=0)

                outputs = detector_session.run(None, {input_name: img_input})

                if model_name == "ArcFace":
                    height_factor = 1.3

                boxes, scores, landmarks = process_yolov8_output(
                    outputs, letterbox_info, height_factor
                )

                all_boxes.append(boxes)
                all_scores.append(scores)
                all_landmarks.append(landmarks)

                # Visualize detections
                if visualize and isinstance(image_path, str) and len(boxes) > 0:
                    debug_dir = "debug_detections"
                    os.makedirs(debug_dir, exist_ok=True)
                    vis_path = os.path.join(
                        debug_dir, os.path.basename(image_path) + "_detect.jpg"
                    )
                    visualize_detections(
                        img, boxes, scores, landmarks, save_path=vis_path
                    )

            # Process detections and get embeddings
            face_embeddings = process_yolo_detections(
                imgs,
                all_boxes,
                all_scores,
                all_landmarks,
                align,
                target_size,
                normalization,
                visualize,
                image_paths,
                model_name,
                face_confidence_threshold,
                detector_backend,
                separate_detections=separate_detections,
            )

            if len(face_embeddings) > 0:
                return True, face_embeddings

            return False, []

    except Exception as e:
        logger.error(f"Error in detect_faces_and_get_embeddings: {str(e)}")
        return False, [e]
