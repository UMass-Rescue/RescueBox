import json
import os

from src.facematch.database_functions import upload_embedding_to_database, query, query_bulk
from src.facematch.face_representation import detect_faces_and_get_embeddings
from src.facematch.utils.logger import log_info
from src.facematch.utils.resource_path import get_config_path


class FaceMatchModel:
    # Function that takes in path to directory of images to upload to database and returns a success or failure message.
    def bulk_upload(self, image_directory_path, collection_name=None):
        try:
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

            # Call face_recognition function for each image file.
            total_files_read = 0
            total_files_uploaded = 0
            embedding_outputs = []

            # Make image_directory_path absolute path since it is stored in database
            image_directory_path = os.path.abspath(image_directory_path)
            for root, dirs, files in os.walk(image_directory_path):
                files.sort()
                for filename in files:
                    image_path = os.path.join(root, filename)
                    if filename.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".bmp")
                    ):
                        # Count the totalnumber of files read
                        total_files_read += 1

                        # Get status and face_embeddings for the image
                        status, value = detect_faces_and_get_embeddings(
                            image_path,
                            model_name,
                            detector_backend,
                            face_confidence_threshold,
                        )
                        if status:
                            total_files_uploaded += 1
                            embedding_outputs.extend(value)

                    # Log info for every 100 files that are successfully converted.
                    if total_files_uploaded % 100 == 0 and total_files_uploaded != 0:
                        log_info(
                            "Successfully converted file "
                            + str(total_files_uploaded)
                            + " / "
                            + str(total_files_read)
                            + " to "
                            "embeddings"
                        )

                    # Upload every 1000 files into database for more efficiency and security.
                    if total_files_uploaded % 1000 == 0 and total_files_uploaded != 0:
                        upload_embedding_to_database(embedding_outputs, collection_name)
                        embedding_outputs = []
                        log_info(
                            "Successfully uploaded "
                            + str(total_files_uploaded)
                            + " / "
                            + str(total_files_read)
                            + " files to "
                            + collection_name
                        )

            if len(embedding_outputs) != 0:
                upload_embedding_to_database(embedding_outputs, collection_name)
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
            return f"An error occurred: {str(e)}"

    # Function that takes in path to image and returns all images that have the same person.
    def find_face(
        self, image_file_path, threshold=None, collection_name=None
    ):
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
                )
                matching_image_paths = []
                # If image has a valid face, perform similarity check
                if status:
                    output = query(collection_name, embedding_outputs, n_results=10, threshold=threshold)
                    # for embedding_output in embedding_outputs:
                        # if toggle_faiss:
                        #     # Use Faiss
                        #     output = cosine_similarity_search_faiss(
                        #         embedding_output["embedding"],
                        #         database_path,
                        #         threshold=threshold,
                        #     )
                        # else:
                        #     # Use linear similarity search
                        #     output = cosine_similarity_search(
                        #         embedding_output["embedding"],
                        #         database_path,
                        #         threshold=threshold,
                        #     )
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
        self, query_directory, threshold=None, collection_name=None, similarity_filter=True
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
            all_embedding_outputs = []
            all_matching_image_paths = []
            
            img_files = os.listdir(query_directory)
            img_files.sort()
            for idx, filename in enumerate(img_files): 
                file_path = os.path.join(query_directory, filename)
                if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                    status, embedding_outputs = detect_faces_and_get_embeddings(
                        file_path,
                        model_name,
                        detector_backend,
                        face_confidence_threshold,
                    )
                if status:
                    all_embedding_outputs.append(embedding_outputs)
                else:
                    all_embedding_outputs.append([])

                num_embeddings = len(all_embedding_outputs)
                
                if num_embeddings % query_batch_size == 0 and num_embeddings != 0:
                    matching_image_paths = query_bulk(collection_name, all_embedding_outputs, 10, threshold, similarity_filter)
                    all_embedding_outputs = []
                    all_matching_image_paths.extend(matching_image_paths)
                    log_info(f"Query: {img_files[idx - num_embeddings+1]}  Match: {matching_image_paths[0]}")

            if len(all_embedding_outputs) != 0:
                    matching_image_paths = query_bulk(collection_name, all_embedding_outputs, 10, threshold, similarity_filter)
                    all_matching_image_paths.extend(matching_image_paths)
            

            results = dict(zip(img_files, all_matching_image_paths))
            return True, results
            
        except Exception as e:
            return False, f"An error occurred: {str(e)}"
