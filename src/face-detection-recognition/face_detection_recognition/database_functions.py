import hashlib
import pandas as pd
import numpy as np
import chromadb
from chromadb.config import Settings
import json
from dotenv import load_dotenv
import os
import platform
import re
from pathlib import Path
from typing import Dict, Optional
from contextvars import ContextVar

from face_detection_recognition.utils.resource_path import get_config_path

# Segment after .../Documents/ — e.g. demo1, demo2, demo3 under /home/user/Documents/demo3/...
_DOCUMENTS_SCOPE = re.compile(r"[/\\]Documents[/\\]([^/\\]+)", re.IGNORECASE)
_VALID_DEMO_SCOPE = re.compile(r"^demo[0-9]+$", re.IGNORECASE)
# Per–RescueBox-user Chroma subfolder (stable hash of explicit user id from X-RescueBox-User-Id)
_VALID_USER_SCOPE = re.compile(r"^u_[a-f0-9]{16}$")

_vector_db_cache: Dict[tuple, "Vector_Database"] = {}

# Set by FastAPI (cli_to_api) from header X-RescueBox-User-Id for each request; isolates collections per user.
facematch_rescuebox_user_id: ContextVar[Optional[str]] = ContextVar(
    "facematch_rescuebox_user_id", default=None
)


def user_scope_from_rescuebox_user_id(user_id: str) -> str:
    """Deterministic folder name under ~/.rescueBox-desktop/facematch/<scope>/ for this app user."""
    h = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:16]
    return f"u_{h}"


def facematch_demo_scope_from_path(path: Optional[str]) -> Optional[str]:
    """
    When the path is under .../Documents/<folder>/..., return <folder> if it matches
    ``demo`` + digits (e.g. demo3). Used to isolate Chroma persistence per demo user folder.

    Paths that do not contain a demo scope use the legacy default store (no subfolder).
    """
    if not path:
        return None
    norm = os.path.normpath(str(path)).replace("\\", "/")
    m = _DOCUMENTS_SCOPE.search(norm)
    if not m:
        return None
    segment = m.group(1)
    return segment if _VALID_DEMO_SCOPE.fullmatch(segment) else None


def get_vector_database(demo_scope: Optional[str] = None) -> "Vector_Database":
    """
    Return a cached Vector_Database for the given demo scope (or legacy default when None).

    ``demo_scope`` must match ``demo[0-9]+``, a per-user scope ``u_<16 hex>``, or be None.
    """
    if demo_scope is not None:
        if not (
            _VALID_DEMO_SCOPE.fullmatch(demo_scope)
            or _VALID_USER_SCOPE.fullmatch(demo_scope)
        ):
            raise ValueError(f"Invalid facematch scope: {demo_scope!r}")
    cache_key = (os.environ.get("IS_TESTING"), demo_scope)
    if cache_key not in _vector_db_cache:
        _vector_db_cache[cache_key] = Vector_Database(demo_scope=demo_scope)
    return _vector_db_cache[cache_key]


def vector_db_for_current_request(path_hint: Optional[str] = None) -> "Vector_Database":
    """
    Select Chroma store for the current HTTP request.

    When ``facematch_rescuebox_user_id`` is set (from ``X-RescueBox-User-Id``), use that user's
    isolated store so collection lists and uploads match across find/bulk/delete flows.

    Otherwise use path-based ``.../Documents/demoN/...`` scope or the legacy default store.
    """
    uid = facematch_rescuebox_user_id.get()
    if uid:
        return get_vector_database(user_scope_from_rescuebox_user_id(uid))
    scope = facematch_demo_scope_from_path(path_hint) if path_hint else None
    return get_vector_database(scope)


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
    def __init__(self, demo_scope: Optional[str] = None):
        """
        Persistent Chroma storage lives under ``~/.rescueBox-desktop/facematch`` (or Windows
        equivalent). When ``demo_scope`` is set (e.g. ``demo3``), data is stored in a
        subdirectory so different demo users do not share embeddings even for the same
        logical collection name.
        """
        if demo_scope is not None and not (
            _VALID_DEMO_SCOPE.fullmatch(demo_scope)
            or _VALID_USER_SCOPE.fullmatch(demo_scope)
        ):
            raise ValueError(f"Invalid facematch scope: {demo_scope!r}")
        self.demo_scope = demo_scope
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
            if demo_scope:
                db_path = db_path / demo_scope
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
