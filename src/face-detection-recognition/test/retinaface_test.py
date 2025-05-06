import os
import logging
import numpy as np
import cv2

from face_detection_recognition.utils.retinaface_utils import (
    detect_with_retinaface,
    create_square_bounds_from_landmarks,
    crop_face_for_facenet512,
    normalize_face,
    prepare_for_embedding,
)
from face_detection_recognition.utils.yolo_utils import get_target_size

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    # Define paths - adjust these to your specific setup
    model_dir = "facematch/facematch/models/"
    model_path = os.path.join(model_dir, "retinaface-resnet50.onnx")
    image_paths = [
        "resources/sample.jpeg",
        # Add more image paths as needed
    ]

    # Create visualization directory
    viz_dir = "visualization"
    os.makedirs(viz_dir, exist_ok=True)

    for image_path in image_paths:
        if not os.path.exists(model_path):
            logger.error(f"Model not found: {model_path}")
            continue

        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            continue

        try:
            logger.info(f"Processing image: {image_path}")

            # Detect faces using RetinaFace
            boxes, scores, landmarks = detect_with_retinaface(
                image_path=image_path,
                model_path=model_path,
                visualize=True,
                confidence_threshold=0.02,
            )

            # Read image
            img = cv2.imread(image_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Detailed face processing and visualization
            if len(boxes) > 0:
                logger.info(f"Detected {len(boxes)} faces")

                for i, (box, score, landmark) in enumerate(
                    zip(boxes, scores, landmarks)
                ):
                    # Create visualization steps
                    steps_viz = []

                    # 1. Original image with detection
                    viz_img = img.copy()
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(viz_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(
                        viz_img,
                        f"Score: {score:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        2,
                    )
                    steps_viz.append(("1_original_detection", viz_img))

                    # 2. Landmarks visualization
                    landmark_viz = img.copy()
                    if landmark:
                        for j, point in enumerate(landmark):
                            x, y = map(int, point)
                            cv2.circle(landmark_viz, (x, y), 3, (0, 255, 0), -1)
                            cv2.putText(
                                landmark_viz,
                                str(j),
                                (x + 3, y + 3),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.3,
                                (0, 0, 255),
                                1,
                            )
                    steps_viz.append(("2_landmarks", landmark_viz))

                    # 3. Landmark-based bounding box
                    if landmark and len(landmark) >= 5:
                        landmark_box_viz = img.copy()
                        improved_box = create_square_bounds_from_landmarks(
                            landmark, img.shape, scale_factor=3.0
                        )
                        if improved_box:
                            lx1, ly1, lx2, ly2 = improved_box
                            cv2.rectangle(
                                landmark_box_viz, (lx1, ly1), (lx2, ly2), (0, 255, 0), 2
                            )
                            cv2.putText(
                                landmark_box_viz,
                                "Landmark Box",
                                (lx1, ly1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (0, 255, 0),
                                2,
                            )
                            steps_viz.append(("3_landmark_box", landmark_box_viz))

                    # 4. Face extraction
                    if landmark and len(landmark) >= 5:
                        improved_box = create_square_bounds_from_landmarks(
                            landmark, img.shape, scale_factor=4.0
                        )
                        if improved_box:
                            x1, y1, x2, y2 = improved_box

                    face = img_rgb[y1:y2, x1:x2].copy()
                    face_img = cv2.cvtColor(face, cv2.COLOR_RGB2BGR)
                    steps_viz.append(("4_extracted_face", face_img))

                    # 5. Crop face
                    cropped_face = crop_face_for_facenet512(face)
                    cropped_face_img = cv2.cvtColor(cropped_face, cv2.COLOR_RGB2BGR)
                    steps_viz.append(("5_cropped_face", cropped_face_img))

                    # 6. Normalize face
                    model_name = "Facenet512"
                    target_size = get_target_size(model_name)
                    normalized_face = normalize_face(
                        cropped_face, target_size, model_name, True
                    )
                    normalized_face_img = cv2.cvtColor(
                        (normalized_face * 255).astype(np.uint8), cv2.COLOR_RGB2BGR
                    )
                    steps_viz.append(("6_normalized_face", normalized_face_img))

                    # 7. Prepare for embedding
                    final_face = prepare_for_embedding(
                        normalized_face, model_name, True
                    )
                    final_face_img = cv2.cvtColor(final_face, cv2.COLOR_RGB2BGR)
                    steps_viz.append(("7_final_face", final_face_img))

                    # Save visualizations
                    base_filename = os.path.basename(image_path).split(".")[0]
                    for step_name, step_img in steps_viz:
                        output_path = os.path.join(
                            viz_dir, f"{base_filename}_face{i}_{step_name}.jpg"
                        )
                        cv2.imwrite(output_path, step_img)
                        logger.info(f"Saved visualization: {output_path}")

            else:
                logger.warning(f"No faces detected in {image_path}")

        except Exception as e:
            logger.error(f"Error processing {image_path}: {e}")


if __name__ == "__main__":
    main()
