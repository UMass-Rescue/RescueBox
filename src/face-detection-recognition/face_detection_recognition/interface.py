import json
import os

from face_detection_recognition.database_functions import Vector_Database
from face_detection_recognition.face_representation import (
    detect_faces_and_get_embeddings,
)
from face_detection_recognition.utils.logger import log_info
from face_detection_recognition.utils.resource_path import get_config_path


class FaceMatchModel:
    def __init__(self):
        self.DB = Vector_Database()

    # Function that takes in path to directory of images to upload to database and returns a success or failure message.
    def bulk_upload(self, image_directory_path, collection_name=None):
        try:
            upload_batch_size = 100
            # Get database from config file.
            if collection_name is None:
                config_path = get_config_path("db_config.json")
                with open(config_path, "r") as config_file:
                    config = json.load(config_file)
                collection_name = config["collection_name"]

            # Get models from config file.
            config_path = get_config_path("model_config.json")
            with open(config_path, "r") as config_file:
                config = json.load(config_file)
            model_name = config["model_name"]
            detector_backend = config["detector_backend"]
            face_confidence_threshold = config["face_confidence_threshold"]

            # Make image_directory_path absolute path since it is stored in database
            image_directory_path = os.path.abspath(image_directory_path)

            img_paths = []

            for root, dirs, files in os.walk(image_directory_path):
                files.sort()
                for filename in files:
                    if filename.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".bmp")
                    ):
                        img_paths.append(os.path.join(image_directory_path, filename))

            end_idx = 0

            total_files_read = len(img_paths)
            total_files_uploaded = 0

            for batch in range(len(img_paths) // upload_batch_size):
                start_idx = end_idx
                end_idx = start_idx + upload_batch_size
                status, embedding_outputs = detect_faces_and_get_embeddings(
                    img_paths[start_idx:end_idx],
                    model_name,
                    detector_backend,
                    face_confidence_threshold,
                    separate_detections=False,
                )

                total_files_uploaded += upload_batch_size

                self.DB.upload_embedding_to_database(
                    embedding_outputs,
                    collection_name,
                )

                log_info(
                    "Successfully uploaded "
                    + str(total_files_uploaded)
                    + " / "
                    + str(total_files_read)
                    + " files to "
                    + collection_name
                )
            if (len(img_paths) % upload_batch_size) != 0:
                status, embedding_outputs = detect_faces_and_get_embeddings(
                    img_paths[end_idx:],
                    model_name,
                    detector_backend,
                    face_confidence_threshold,
                    separate_detections=False,
                )
                self.DB.upload_embedding_to_database(
                    embedding_outputs,
                    collection_name,
                )

                total_files_uploaded += len(img_paths[end_idx:])
                log_info(
                    "Successfully uploaded "
                    + str(total_files_uploaded)
                    + " / "
                    + str(total_files_read)
                    + " files to "
                    + collection_name
                )

            return (
                "Successfully uploaded "
                + str(total_files_uploaded)
                + " / "
                + str(total_files_read)
                + " files to "
                + collection_name
            )
        except Exception as e:
            return f"Bulk Upload Error: {str(e)}"

    # Function that takes in path to image and returns all images that have the same person.
    def find_face(self, image_file_path, threshold=None, collection_name=None):
        try:
            # Get models from config file.
            config_path = get_config_path("model_config.json")
            with open(config_path, "r") as config_file:
                config = json.load(config_file)
            model_name = config["model_name"]
            detector_backend = config["detector_backend"]
            face_confidence_threshold = config["face_confidence_threshold"]
            if threshold is None:
                threshold = config["cosine-threshold"]
            # Call face_recognition function and perform similarity check to find identical persons.
            filename = os.path.basename(image_file_path)
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                status, embedding_outputs = detect_faces_and_get_embeddings(
                    image_file_path,
                    model_name,
                    detector_backend,
                    face_confidence_threshold,
                    separate_detections=False,
                )
                matching_image_paths = []
                # If image has a valid face, perform similarity check
                if status:
                    output = self.DB.query(
                        collection_name,
                        embedding_outputs,
                        n_results=10,
                        threshold=threshold,
                    )
                    matching_image_paths.extend(output)
                    return True, matching_image_paths
                else:
                    return False, "Error: Provided image does not have any face"
            else:
                return False, "Error: Provided file is not of image type"
        except Exception as e:
            return False, f"An error occurred: {str(e)}"

    # Function that takes in path to image and returns all images that have the same person.
    def find_face_bulk(
        self,
        query_directory,
        threshold=None,
        collection_name=None,
        similarity_filter=True,
    ):
        try:
            query_batch_size = 100

            # Get models from config file.
            config_path = get_config_path("model_config.json")
            with open(config_path, "r") as config_file:
                config = json.load(config_file)
            model_name = config["model_name"]
            detector_backend = config["detector_backend"]
            face_confidence_threshold = config["face_confidence_threshold"]
            if threshold is None:
                threshold = config["cosine-threshold"]
            # Call face_recognition function and perform similarity check to find identical persons.
            all_matching_image_paths = []

            img_files = os.listdir(query_directory)
            img_files.sort()
            img_paths = []
            for filename in img_files:
                if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                    img_paths.append(os.path.join(query_directory, filename))

            end_idx = 0

            for batch in range(len(img_paths) // query_batch_size):
                start_idx = end_idx
                end_idx = start_idx + query_batch_size
                status, embedding_outputs = detect_faces_and_get_embeddings(
                    img_paths[start_idx:end_idx],
                    model_name,
                    detector_backend,
                    face_confidence_threshold,
                    separate_detections=True,
                )

                matching_image_paths = self.DB.query_bulk(
                    collection_name,
                    embedding_outputs,
                    10,
                    threshold,
                    similarity_filter,
                )
                all_matching_image_paths.extend(matching_image_paths)

            if (len(img_paths) % query_batch_size) != 0:
                status, embedding_outputs = detect_faces_and_get_embeddings(
                    img_paths[end_idx:],
                    model_name,
                    detector_backend,
                    face_confidence_threshold,
                    separate_detections=True,
                )

                matching_image_paths = self.DB.query_bulk(
                    collection_name,
                    embedding_outputs,
                    10,
                    threshold,
                    similarity_filter,
                )
                all_matching_image_paths.extend(matching_image_paths)

            results = dict(zip(img_files, all_matching_image_paths))
            return True, results

        except Exception as e:
            return False, f"An error occurred: {str(e)}"
