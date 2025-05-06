import cv2
from deepface import DeepFace


def check_face_recognition_edge_cases(img1_path, img2_path):
    result = DeepFace.verify(
        img1_path=img1_path,
        img2_path=img2_path,
        model_name="ArcFace",
        enforce_detection=True,
        detector_backend="yolov8",
    )
    print(result)


def check_face_detection_edge_cases(image_path):
    img = cv2.imread(image_path)
    results = DeepFace.represent(
        image_path,
        model_name="ArcFace",
        detector_backend="yolov8",
        enforce_detection=True,
    )

    # Iterate over the results
    for i, result in enumerate(results):
        # Get face region for drawing bounding box
        x, y, width, height = (
            result["facial_area"]["x"],
            result["facial_area"]["y"],
            result["facial_area"]["w"],
            result["facial_area"]["h"],
        )

        if result["face_confidence"] > 0.7:
            key = f"face_{i + 1}"  # Creating a unique identifier for each face

            # Draw a rectangle around the detected face
            cv2.rectangle(img, (x, y), (x + width, y + height), (255, 0, 0), 2)
            cv2.putText(
                img, key, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2
            )

    # Display the image with bounding boxes
    cv2.imshow("Detected Faces", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


image1 = "../resources/LFWdataset/sample_queries/Aaron_Peirsol_0004.jpg"
image2 = "../resources/LFWdataset/sample_queries/Aaron_Sorkin_0001.jpg"
check_face_detection_edge_cases(image1)
check_face_detection_edge_cases(image2)
check_face_recognition_edge_cases(image1, image2)
