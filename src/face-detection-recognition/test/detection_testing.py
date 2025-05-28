from face_detection_recognition.face_representation import (
    detect_faces_and_get_embeddings,
)
import os

path = "/Users/davidthibodeau/Desktop/CS596E/group_proj/face-detection-recognition/face_detection_recognition/models/yolov8-face-detection.onnx"
print(f"Model exists: {os.path.exists(path)}")

# Test with a single image
image_path = "resources/sample_images/me.png"
success, embeddings = detect_faces_and_get_embeddings(
    image_path,
    model_name="ArcFace",
    detector_backend="yolov8",
    face_confidence_threshold=0.7,
    visualize=True,
)

if success:
    print(f"Found {len(embeddings)} faces")
    for i, face in enumerate(embeddings):
        print(f"Face {i+1}: confidence={face['confidence']:.2f}")
else:
    print("No faces detected")
