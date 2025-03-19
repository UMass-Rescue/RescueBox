import json
import os
import logging
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from rb_facematch.src.facematch.database_functions import upload_embedding_to_database
from rb_facematch.src.facematch.face_representation import detect_faces_and_get_embeddings
from rb_facematch.src.facematch.similarity_search import (cosine_similarity_search,
                                             cosine_similarity_search_faiss)

from rb_facematch.src.facematch.utils.resource_path import (get_config_path,
                                               get_resource_path)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FaceMatchModel:
    # Function that takes in path to directory of images to upload to database and returns a success or failure message.
    def bulk_upload(self, image_directory_path, database_path=None):
        try:
            # Get database from config file.
            if database_path is None:
                config_path = get_config_path("db_config.json")
                with open(config_path, "r") as config_file:
                    config = json.load(config_file)
                database_path = get_resource_path(config["database_path"])
            else:
                database_path = get_resource_path(database_path)

            logger.debug(database_path)

            # Get models from config file.
            config_path = get_config_path("model_config.json")
            with open(config_path, "r") as config_file:
                config = json.load(config_file)
            model_name = config["model_name"]
            detector_backend = config["detector_backend"]
            face_confidence_threshold = config["face_confidence_threshold"]

            # Call face_recognition function for each image file.
            total_files_read = 0
            total_files_uploaded = 0
            embedding_outputs = []

            # Make image_directory_path absolute path since it is stored in database
            image_directory_path = os.path.abspath(image_directory_path)
            for root, dirs, files in os.walk(image_directory_path):
                for filename in files:
                    image_path = os.path.join(root, filename)
                    if filename.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".bmp")
                    ):
                        # Count the totalnumber of files read
                        total_files_read += 1
                        logger.debug("debug detect_faces_and_get_embeddings")
                        # Get status and face_embeddings for the image
                        status, value = detect_faces_and_get_embeddings(
                            image_path,
                            model_name,
                            detector_backend,
                            face_confidence_threshold,
                        )
                        logger.debug(image_path)
                        logger.debug(status)
                        if status:
                            total_files_uploaded += 1
                            embedding_outputs.extend(value)

                    # Log info for every 100 files that are successfully converted.
                    if total_files_uploaded % 100 == 0 and total_files_uploaded != 0:
                        logger.debug(
                            "Successfully converted file "
                            + str(total_files_uploaded)
                            + " / "
                            + str(total_files_read)
                            + " to "
                            "embeddings"
                        )

                    # Upload every 1000 files into database for more efficiency and security.
                    if total_files_uploaded % 1000 == 0 and total_files_uploaded != 0:
                        upload_embedding_to_database(embedding_outputs, database_path)
                        embedding_outputs = []
                        logger.debug(
                            "Successfully uploaded "
                            + str(total_files_uploaded)
                            + " / "
                            + str(total_files_read)
                            + " files to "
                            + database_path
                        )

            if len(embedding_outputs) != 0:
                upload_embedding_to_database(embedding_outputs, database_path)
                logger.debug(
                    "Successfully uploaded "
                    + str(total_files_uploaded)
                    + " / "
                    + str(total_files_read)
                    + " files to "
                    + database_path
                )

            if total_files_uploaded != total_files_read:
                return f"An error occurred: {str(total_files_uploaded) + ' files uploaded'}"

            return (
                "Successfully uploaded "
                + str(total_files_uploaded)
                + " / "
                + str(total_files_read)
                + " files to "
                + database_path
            )
        except Exception as e:
            return f"An error occurred: {str(e)}"

    # Function that takes in path to image and returns all images that have the same person.
    def find_face(
        self, image_file_path, threshold=None, database_path=None, toggle_faiss=True
    ):
        try:
            # Get database from config file.
            if database_path is None:
                config_path = get_config_path("db_config.json")
                with open(config_path, "r") as config_file:
                    config = json.load(config_file)
                database_path = get_resource_path(config["database_path"])
            else:
                database_path = get_resource_path(database_path)

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
                )
                matching_image_paths = []

                # If image has a valid face, perform similarity check
                if status:
                    for embedding_output in embedding_outputs:
                        if toggle_faiss:
                            # Use Faiss
                            output = cosine_similarity_search_faiss(
                                embedding_output["embedding"],
                                database_path,
                                threshold=threshold,
                            )
                        else:
                            # Use linear similarity search
                            output = cosine_similarity_search(
                                embedding_output["embedding"],
                                database_path,
                                threshold=threshold,
                            )
                        for element in output:
                            if element not in matching_image_paths:
                                matching_image_paths.append(element)
                    return True, matching_image_paths
                else:
                    return False, "Error: Provided image does not have any face"
            else:
                return False, "Error: Provided file is not of image type"
        except Exception as e:
            return False, f"An error occurred: {str(e)}"
