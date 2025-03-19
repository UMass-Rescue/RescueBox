from deepface import DeepFace


# Function that takes in path to image and returns a status field and a list of face embeddings and corresponding
# region for all faces in the image.
def detect_faces_and_get_embeddings(
    image_path, model_name, detector_backend, face_confidence_threshold=0
):
    try:
        results = DeepFace.represent(
            image_path,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=True,
        )

        # Check if each face has a high enough confidence score
        face_embeddings = []

        for i, result in enumerate(results):
            if result["face_confidence"] < face_confidence_threshold:
                continue

            embedding = result["embedding"]

            x, y, width, height = (
                result["facial_area"]["x"],
                result["facial_area"]["y"],
                result["facial_area"]["w"],
                result["facial_area"]["h"],
            )

            face_embeddings.append(
                {
                    "image_path": image_path,
                    "embedding": embedding,
                    "bbox": [x, y, width, height],
                }
            )

        # Return False, [] if no faces are above confidence threshold, else return True and the list of face embeddings
        if len(face_embeddings) == 0:
            return False, []
        return True, face_embeddings
    except Exception as e:
        return False, [e]
