import pandas as pd
import numpy as np
import chromadb
from chromadb.config import Settings
import json
from dotenv import load_dotenv
import os
import platform
from pathlib import Path

from face_detection_recognition.utils.resource_path import get_config_path

# Get models from config file.
db_config_path = get_config_path("db_config.json")
with open(db_config_path, "r") as config_file:
    db_config = json.load(config_file)

model_config_path = get_config_path("model_config.json")
with open(model_config_path, "r") as config_file:
    model_config = json.load(config_file)

detector_backend = model_config["detector_backend"]
model_name = model_config["model_name"]
space = db_config["hnsw:space"]
construction_ef = db_config["hnsw:construction_ef"]
search_ef = db_config["hnsw:search_ef"]
M = db_config["hnsw:M"]

load_dotenv()


class Vector_Database:
    def __init__(self):
        testing = os.environ.get("IS_TESTING")
        self.single_indicator = "S"
        self.ensemble_indicator = "E"
        if testing == "true":
            self.client = chromadb.EphemeralClient()
        else:
            settings = Settings(
                anonymized_telemetry=False,
            )
            db_path = Path.home() / ".rescueBox-desktop" / "facematch"
            if platform.system() == "Windows":
                appdata = os.environ.get("APPDATA")
                db_path = Path(appdata) / "RescueBox-Desktop" / "facematch"
            if not db_path.exists():
                db_path.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                settings=settings,
                path=str(db_path),
            )

    def create_full_collection_name(self, base_name, detector, model, isEnsemble):
        return f"{base_name}_{detector.lower()[0:2]}{model.lower()[0:2]}{self.ensemble_indicator if isEnsemble else self.single_indicator}"

    def get_available_collections(self, isEnsemble=False):
        existing_collections = [
            collection.name for collection in self.client.list_collections()
        ]
        collections = list(
            filter(
                lambda name: name.split("_")[-1][-1]
                == (self.ensemble_indicator if isEnsemble else self.single_indicator),
                existing_collections,
            )
        )
        collections = list(
            map(lambda name: "_".join(name.split("_")[:-1]), collections)
        )

        if isEnsemble:
            collections = list(set(collections))

        return collections

    def get_collection(self, collection):
        return self.client.get_or_create_collection(
            name=collection,
            metadata={
                "image_path": "Original path of the uploaded image",
                "hnsw:space": space,
                "hnsw:construction_ef": construction_ef,
                "hnsw:search_ef": search_ef,
                "hnsw:M": M,
            },
        )

    def upload_embedding_to_database(self, data, collection):
        df = pd.DataFrame(data)
        df["bbox"] = df["bbox"].apply(lambda x: ",".join(map(str, x)))

        metadatas = [{"image_path": d["image_path"]} for d in data]

        collection = self.get_collection(collection)
        collection.add(
            embeddings=list(df["embedding"]),
            metadatas=metadatas,
            ids=list(df["sha256_image"]),
        )

    def query(self, collection, data, n_results, threshold):
        query_vectors = [image["embedding"] for image in data]
        collection = self.get_collection(collection)

        result = collection.query(
            query_embeddings=query_vectors,
            n_results=n_results,
            include=["metadatas", "distances", "embeddings"],
        )

        # Flatten results and include index
        data = []
        for idx, (ids, distances, embeddings, metadatas) in enumerate(
            zip(
                result["ids"],
                result["distances"],
                result["embeddings"],
                result["metadatas"],
            )
        ):
            for image_id, distance, embedding, metadata in zip(
                ids, distances, embeddings, metadatas
            ):
                data.append(
                    {
                        "query_index": idx,  # Index of the original face in the query
                        "id": image_id,
                        "distance": distance,
                        "embedding": embedding.tolist(),
                        "img_path": metadata["image_path"],
                    }
                )

        # Convert to DataFrame
        result_df = pd.DataFrame(data)

        result_df["similarity"] = 1 - result_df["distance"]

        if threshold is not None:
            # Filter the DataFrame based on the threshold
            result_df = result_df[result_df["similarity"] >= threshold]

        # sort results by similarity in descending order
        result_df = result_df.sort_values(
            by=["query_index", "similarity"], ascending=[True, False]
        )

        top_img_paths = result_df["img_path"].to_list()

        return top_img_paths

    def query_bulk(self, collection, data, n_results, threshold, similarity_filter):
        vectors_per_query = np.array(list(map(lambda query: len(query), data)))
        vectors_per_query_idx = np.cumsum(vectors_per_query)[:-1]
        query_vectors = [face["embedding"] for query in data for face in query]
        collection = self.get_collection(collection)
        result = collection.query(
            query_embeddings=query_vectors,
            n_results=n_results,
            include=["metadatas", "distances", "embeddings"],
        )

        for param in ["ids", "distances", "embeddings", "metadatas"]:
            result[param] = np.split(result[param], vectors_per_query_idx)

        # Flatten results and include index
        data = []
        for query_idx, (q_ids, q_distances, q_embeddings, q_metadatas) in enumerate(
            zip(
                result["ids"],
                result["distances"],
                result["embeddings"],
                result["metadatas"],
            )
        ):
            if len(q_ids) == 0:  # If the query has no results, insert a placeholder
                data.append(
                    {
                        "query_index": query_idx,
                        "face_idx": 0,
                        "id": None,
                        "distance": 1,
                        "embedding": None,
                        "img_path": None,
                    }
                )
                continue
            for face_idx, (f_ids, f_distances, f_embeddings, f_metadatas) in enumerate(
                zip(q_ids, q_distances, q_embeddings, q_metadatas)
            ):
                for image_id, distance, embedding, metadata in zip(
                    f_ids, f_distances, f_embeddings, f_metadatas
                ):
                    data.append(
                        {
                            "query_index": query_idx,
                            "face_idx": face_idx,
                            "id": image_id,
                            "distance": distance,
                            "embedding": embedding.tolist(),
                            "img_path": metadata["image_path"],
                        }
                    )

        # Convert to DataFrame
        result_df = pd.DataFrame(data)

        result_df["similarity"] = 1 - result_df["distance"]

        # sort results by similarity in descending order
        result_df = result_df.sort_values(
            by=["query_index", "face_idx", "similarity"], ascending=[True, True, False]
        )

        # Function to filter paths based on similarity threshold, but keep an empty list if none qualify
        def filter_by_similarity(group):
            paths = group.loc[group["similarity"] >= threshold, "img_path"].tolist()
            return paths if paths else []

        # Function to return all results with their similarities as an array of dictionaries for testing purposes
        def extract_paths(group):
            paths = group.loc[:, ["similarity", "img_path", "face_idx"]].to_dict(
                orient="records"
            )
            return paths if paths else []

        # Group by 'index' and extract paths while preserving order
        if similarity_filter:
            top_img_paths = (
                result_df.groupby("query_index", sort=False)
                .apply(filter_by_similarity)
                .tolist()
            )
        else:
            top_img_paths = (
                result_df.groupby("query_index", sort=False)
                .apply(extract_paths)
                .tolist()
            )

        return top_img_paths
