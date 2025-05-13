import os
import cv2
import numpy as np
import logging
import matplotlib.pyplot as plt
import matplotlib

from face_detection_recognition.hash import sha256_image

matplotlib.use("Agg")

from face_detection_recognition.utils.get_batch_embeddings import get_embedding

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def visualize_detections(image_path, boxes, scores, landmarks=None, save_path=None):
    """Visualize face detections with bounding boxes and optional landmarks"""
    # Load image
    if isinstance(image_path, str):
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    else:
        img = image_path.copy()

    # Draw detections
    for i, (box, score) in enumerate(zip(boxes, scores)):
        x1, y1, x2, y2 = map(int, box)

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        score_text = f"{score:.2f}"
        cv2.putText(
            img,
            score_text,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

        if landmarks and i < len(landmarks) and landmarks[i] is not None:
            for point in landmarks[i]:
                x, y = map(int, point)
                cv2.circle(img, (x, y), 3, (255, 0, 0), -1)

    plt.figure(figsize=(12, 8))
    plt.imshow(img)
    plt.axis("off")

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)

    plt.close()


def get_target_size(model_name):
    """Get target size based on the embedding model"""
    if model_name == "Facenet512":
        return (160, 160)
    elif model_name == "ArcFace":
        return (112, 112)
    else:
        return (224, 224)


def crop_face_for_facenet_embedding(face_img):

    if face_img is None or face_img.size == 0:
        return None

    h, w = face_img.shape[:2]
    ratio = h / w

    # Calculate crop margins
    top_margin = int(h * 0.12)  # 12% from top
    bottom_margin = int(h * 0.2)  # 20% from bottom
    left_margin = int(w * 0.16 / ratio)  # 16% from left
    right_margin = int(w * 0.16 / ratio)  # 16% from right

    y_start = top_margin
    y_end = h - bottom_margin
    x_start = left_margin
    x_end = w - right_margin

    # Ensure valid dimensions
    if y_end <= y_start or x_end <= x_start:
        return face_img

    cropped_face = face_img[y_start:y_end, x_start:x_end]

    return cropped_face


def crop_face_for_embedding(face_img):
    """
    Crop a face image to prepare it for embedding, ensuring a square output.
    """
    if face_img is None or face_img.size == 0:
        return None

    h, w = face_img.shape[:2]

    top_margin = int(h * 0.12)  # 12% from top
    bottom_margin = int(h * 0.15)  # 15% from bottom
    left_margin = int(w * 0.10)  # 10% from left
    right_margin = int(w * 0.10)  # 10% from right

    # Calculate initial cropping coordinates
    y_start = top_margin
    y_end = h - bottom_margin
    x_start = left_margin
    x_end = w - right_margin

    # Ensure valid dimensions
    if y_end <= y_start or x_end <= x_start:
        # If invalid crop dimensions, keep original but make square
        center_x = w // 2
        center_y = h // 2
        side_length = min(w, h)

        x_start = max(0, center_x - side_length // 2)
        y_start = max(0, center_y - side_length // 2)
        x_end = min(w, x_start + side_length)
        y_end = min(h, y_start + side_length)

        return face_img[y_start:y_end, x_start:x_end]

    # Calculate dimensions of initially cropped area
    crop_h = y_end - y_start
    crop_w = x_end - x_start

    # Make it square by using the smaller dimension
    if crop_h != crop_w:
        if crop_h > crop_w:
            # Height is larger, center vertically
            diff = crop_h - crop_w
            y_start += diff // 2
            y_end = y_start + crop_w
        else:
            # Width is larger, center horizontally
            diff = crop_w - crop_h
            x_start += diff // 2
            x_end = x_start + crop_h

    y_start = max(0, y_start)
    y_end = min(h, y_end)
    x_start = max(0, x_start)
    x_end = min(w, x_end)

    final_size = min(y_end - y_start, x_end - x_start)
    center_y = (y_start + y_end) // 2
    center_x = (x_start + x_end) // 2

    y_start = max(0, center_y - final_size // 2)
    y_end = min(h, y_start + final_size)
    x_start = max(0, center_x - final_size // 2)
    x_end = min(w, x_start + final_size)

    # Check if we need to adjust again due to boundary constraints
    if y_end - y_start != x_end - x_start:
        final_size = min(y_end - y_start, x_end - x_start)
        y_end = y_start + final_size
        x_end = x_start + final_size

    # Apply cropping
    cropped_face = face_img[y_start:y_end, x_start:x_end]

    return cropped_face


def process_yolov8_output(outputs, letterbox_info=None, height_factor=1.25):
    """Process YOLOv8 face detection output in grid format (1, 5, 8400). Creates square bounding boxes and returns them in a format compatible with the rest of the pipeline."""
    scores, landmarks = [], []

    # YOLOv8-face in grid format
    output = outputs[0][0]  # Shape (5, 8400)

    confidence = output[4]  # Shape (8400,)

    # Get indices of potential faces (confidence above threshold)
    threshold = 0.7  # Adjust as needed
    mask = confidence > threshold
    indices = np.nonzero(mask)[0]

    logger.info(f"Found {len(indices)} potential faces above threshold {threshold}")

    if len(indices) == 0:
        return [], [], []

    # Extract filtered boxes
    x = output[0][indices]
    y = output[1][indices]
    w = output[2][indices]
    h = output[3][indices]
    conf = confidence[indices]

    # Convert to corner format (x1, y1, x2, y2)
    x1 = x - w / 2
    y1 = y - h / 2
    x2 = x + w / 2
    y2 = y + h / 2

    # Adjust for letterbox
    if letterbox_info:
        scale = letterbox_info["scale"]
        pad_w = letterbox_info["pad_w"]
        pad_h = letterbox_info["pad_h"]

        # Remove padding and rescale
        x1 = (x1 - pad_w) / scale
        y1 = (y1 - pad_h) / scale
        x2 = (x2 - pad_w) / scale
        y2 = (y2 - pad_h) / scale

        # Clip to image boundaries
        orig_w, orig_h = letterbox_info["orig_size"]
        x1 = np.clip(x1, 0, orig_w)
        y1 = np.clip(y1, 0, orig_h)
        x2 = np.clip(x2, 0, orig_w)
        y2 = np.clip(y2, 0, orig_h)

    # Apply NMS on initial boxes for efficiency
    initial_boxes = [
        [float(x1[i]), float(y1[i]), float(x2[i]), float(y2[i])]
        for i in range(len(indices))
    ]
    scores = [float(conf[i]) for i in range(len(indices))]
    landmarks = [None] * len(indices)

    if len(initial_boxes) > 1:
        try:
            nms_indices = cv2.dnn.NMSBoxes(
                initial_boxes, scores, score_threshold=threshold, nms_threshold=0.45
            )

            # Filter initial boxes, scores, and landmarks based on NMS
            filtered_boxes = [initial_boxes[i] for i in nms_indices]
            filtered_scores = [scores[i] for i in nms_indices]
            filtered_landmarks = [landmarks[i] for i in nms_indices]

            initial_boxes, scores, landmarks = (
                filtered_boxes,
                filtered_scores,
                filtered_landmarks,
            )
            logger.info(
                f"NMS reduced detections from {len(indices)} to {len(initial_boxes)}"
            )
        except Exception as e:
            logger.error(f"Error applying NMS: {e}")

    # Now create square boxes
    square_boxes = []
    for box in initial_boxes:
        x1, y1, x2, y2 = box

        current_height = y2 - y1

        # Apply height factor to expand height
        expanded_height = current_height * height_factor

        # Center point
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        side_length = expanded_height

        # Calculate new coordinates to make a square box
        new_x1 = center_x - (side_length / 2)
        new_y1 = center_y - (side_length / 2)
        new_x2 = center_x + (side_length / 2)
        new_y2 = center_y + (side_length / 2)

        # Ensure box is within image boundaries
        if letterbox_info:
            orig_w, orig_h = letterbox_info["orig_size"]
            new_x1 = max(0, new_x1)
            new_y1 = max(0, new_y1)
            new_x2 = min(orig_w, new_x2)
            new_y2 = min(orig_h, new_y2)

        square_boxes.append([new_x1, new_y1, new_x2, new_y2])

    logger.info(f"Final face count: {len(square_boxes)}")
    return square_boxes, scores, landmarks


def extract_face(img, box, landmark, detector_backend):
    """Extract face region based on bounding box"""
    img_height, img_width = img.shape[:2]

    if len(box) == 4:
        x1, y1, x2, y2 = map(int, box)

    else:
        logger.warning(f"Invalid box format: {box}")
        return None, None

    # Ensure coordinates are within image boundaries
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(img_width, x2)
    y2 = min(img_height, y2)

    # Check if box is valid
    if x2 <= x1 or y2 <= y1 or x2 > img_width or y2 > img_height:
        logger.warning(f"Invalid face coordinates: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
        return None, None

    # Extract face region
    try:
        face = img[y1:y2, x1:x2]
        if face.size == 0:
            logger.warning("Extracted face has zero size")
            return None, None
    except Exception as e:
        logger.error(f"Error extracting face: {e}")
        return None, None

    # Create region info with landmarks
    region = {
        "x": x1,
        "y": y1,
        "w": x2 - x1,
        "h": y2 - y1,
        "left_eye": None,
        "right_eye": None,
    }

    # Add landmarks if available
    if landmark is not None:
        if len(landmark) >= 2:
            region["left_eye"] = (int(landmark[0][0]), int(landmark[0][1]))
            region["right_eye"] = (int(landmark[1][0]), int(landmark[1][1]))

    return face, region


def align_face(face, img, region):
    """Align face based on eye positions"""
    if region["left_eye"] is None or region["right_eye"] is None:
        return face

    left_eye = region["left_eye"]
    right_eye = region["right_eye"]

    # Calculate angle for alignment
    dx = right_eye[0] - left_eye[0]
    dy = right_eye[1] - left_eye[1]
    angle = np.degrees(np.arctan2(dy, dx))

    # Calculate desired eye position based on face dimensions
    face_width, face_height = region["w"], region["h"]
    desired_left_eye_x = 0.35  # Proportion from the left edge
    desired_right_eye_x = 1.0 - desired_left_eye_x

    desired_eye_y = 0.4  # Proportion from the top edge

    desired_dist = (desired_right_eye_x - desired_left_eye_x) * face_width
    actual_dist = np.sqrt((dx**2) + (dy**2))
    scale = desired_dist / actual_dist

    # Calculate rotation center (between the eyes)
    eye_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)

    # Get rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D(eye_center, angle, scale)

    # Update translation component of the matrix
    rotation_matrix[0, 2] += (face_width * 0.5) - eye_center[0]
    rotation_matrix[1, 2] += (face_height * desired_eye_y) - eye_center[1]

    # Apply affine transformation to the original image
    output_size = (face_width, face_height)
    aligned_face = cv2.warpAffine(
        img, rotation_matrix, output_size, flags=cv2.INTER_CUBIC
    )

    y_min = max(0, region["y"] - int(face_height * 0.1))
    y_max = min(img.shape[0], region["y"] + region["h"] + int(face_height * 0.1))
    x_min = max(0, region["x"] - int(face_width * 0.1))
    x_max = min(img.shape[1], region["x"] + region["w"] + int(face_width * 0.1))

    aligned_face = aligned_face[y_min:y_max, x_min:x_max]

    return aligned_face


def normalize_face(face, target_size, model_name, normalization=True):
    """Normalize face for the embedding model"""
    if face is None or face.size == 0:
        logger.warning("Empty face provided to normalize_face")
        return None

    if not normalization:
        return face

    # Resize to target dimensions required by the embedding model
    face_resized = cv2.resize(face, target_size)

    # Convert to the expected format based on embedding model
    if model_name == "Facenet512":
        face_normalized = face_resized.astype(np.float32)
        face_normalized = (face_normalized - 127.5) / 128.0

    elif model_name in ["ArcFace", "SFace"]:
        face_normalized = face_resized.astype(np.float32)
        face_normalized = face_normalized / 255.0
        # Standard normalization
        mean = np.array([0.5, 0.5, 0.5])
        std = np.array([0.5, 0.5, 0.5])
        face_normalized = (face_normalized - mean) / std

    else:
        face_normalized = face_resized.astype(np.float32) / 255.0

    return face_normalized


def prepare_for_embedding(face, model_name, normalization):
    """
    Final preparation to make the face compatible with embedding model's expectations
    """
    # models generally expect uint8 input (0-255)
    # If we've normalized, we need to convert back
    if normalization and face is not None:

        if model_name == "Facenet512":
            # For FaceNet, revert normalization
            face_uint8 = ((face * 128.0) + 127.5).astype(np.uint8)
            return face_uint8

        elif model_name in ["ArcFace", "SFace"]:
            # For ArcFace/SFace, revert normalization
            mean = np.array([0.5, 0.5, 0.5])
            std = np.array([0.5, 0.5, 0.5])
            face_uint8 = ((face * std) + mean) * 255
            face_uint8 = np.clip(face_uint8, 0, 255).astype(np.uint8)
            return face_uint8

        else:
            # Default reversion
            face_uint8 = (face * 255).astype(np.uint8)
            return face_uint8
    else:
        if face is not None:
            return face.astype(np.uint8)
        return None


def process_yolo_detections(
    imgs,
    all_boxes,
    all_scores,
    all_landmarks,
    align=True,
    target_size=None,
    normalization=True,
    visualize=False,
    image_paths=None,
    model_name="ArcFace",
    face_confidence_threshold=0.02,
    detector_backend="yolov8",
    separate_detections=False,
):
    """Process YOLO face detections and generate embeddings."""
    face_embeddings = []
    detections = []
    path_strs = []
    regions = []

    detections_per_image = []
    for boxes, scores, landmarks, image_path, img in zip(
        all_boxes, all_scores, all_landmarks, image_paths, imgs
    ):

        detections_per_image.append(len(boxes))

        if len(boxes) == 0:
            continue

        valid_faces = sum(1 for score in scores if score >= face_confidence_threshold)
        if valid_faces == 0:
            continue

        # Process each detected face
        for i, (box, score) in enumerate(zip(boxes, scores)):
            if score < face_confidence_threshold:
                continue

            landmark = landmarks[i] if landmarks and i < len(landmarks) else None

            face, region = extract_face(img, box, landmark, detector_backend)

            if face is None or face.size == 0:
                continue

            region["confidence"] = float(score)

            # Align face if landmarks available
            if (
                align
                and region["left_eye"] is not None
                and region["right_eye"] is not None
            ):
                face = align_face(face, img, region)

            if model_name == "Facenet512":
                face = crop_face_for_facenet_embedding(face)
                face_normalized = normalize_face(
                    face, target_size, model_name, normalization
                )
                if face_normalized is None:
                    continue

                detection = prepare_for_embedding(
                    face_normalized, model_name, normalization
                )
                if detection is None:
                    continue

            elif model_name == "ArcFace":
                face = crop_face_for_embedding(face)
                face_resized = cv2.resize(face, target_size)
                detection = np.clip(face_resized, 0, 255).astype(np.uint8)

            # Visualize processed faces
            if visualize and isinstance(image_path, str):
                debug_dir = "debug_faces"
                os.makedirs(debug_dir, exist_ok=True)
                face_path = os.path.join(
                    debug_dir, f"{os.path.basename(image_path)}_face_{i}.jpg"
                )
                if isinstance(detection, np.ndarray):
                    cv2.imwrite(face_path, cv2.cvtColor(detection, cv2.COLOR_RGB2BGR))

            detections.append(detection)
            path_strs.append(image_path)
            regions.append(region)

    # Generate embedding
    try:

        embeddings = get_embedding(detections, model_name, "base")

    except Exception as e:
        logger.error(f"Error getting embedding for face {i}: {str(e)}")

    i = 0
    for num_detections in detections_per_image:
        cur_img_face_embeddings = []
        for _ in range(num_detections):
            if embeddings[i] is not None:
                bbox = [
                    regions[i]["x"],
                    regions[i]["y"],
                    regions[i]["w"],
                    regions[i]["h"],
                ]
                image = sha256_image(path_strs[i], bbox)
                cur_img_face_embeddings.append(
                    {
                        "image_path": path_strs[i],
                        "embedding": embeddings[i],
                        "bbox": bbox,
                        "confidence": regions[i]["confidence"],
                        "sha256_image": image,
                        "model_name": model_name,
                    }
                )
            i += 1

        if separate_detections:
            face_embeddings.append(cur_img_face_embeddings)
        else:
            face_embeddings.extend(cur_img_face_embeddings)

    return face_embeddings
