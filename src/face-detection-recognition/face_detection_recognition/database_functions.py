import hashlib
import json
import logging
import os
import re
from collections.abc import Sequence
from contextvars import ContextVar
from functools import lru_cache
from typing import Any

import pandas as pd
from rb.api.database import FaceEmbedding, create_db_and_tables, engine
from rb.api.embedding_storage import FaceEmbeddingStorage
from sqlalchemy import delete, text
from sqlmodel import Session, select

from face_detection_recognition.utils.resource_path import get_config_path

logger = logging.getLogger(__name__)

# Segment after .../Documents/ — e.g. demo1, demo2, demo3 under /home/user/Documents/demo3/...
_DOCUMENTS_SCOPE = re.compile(r"[/\\]Documents[/\\]([^/\\]+)", re.IGNORECASE)
_VALID_DEMO_SCOPE = re.compile(r"^demo[0-9]+$", re.IGNORECASE)
# Per–RescueBox-user scope (stable hash of explicit user id from X-RescueBox-User-Id)
_VALID_USER_SCOPE = re.compile(r"^u_[a-f0-9]{16}$")

_vector_db_cache: dict[tuple, "Vector_Database"] = {}

# Set by FastAPI (cli_to_api) from header X-RescueBox-User-Id for each request; isolates rows per user.
facematch_rescuebox_user_id: ContextVar[str | None] = ContextVar(
    "facematch_rescuebox_user_id", default=None
)


def user_scope_from_rescuebox_user_id(user_id: str) -> str:
    """Deterministic scope key for this app user (was a Chroma subfolder)."""
    h = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:16]
    return f"u_{h}"


def facematch_demo_scope_from_path(path: str | None) -> str | None:
    """
    When the path is under .../Documents/<folder>/..., return <folder> if it matches
    ``demo`` + digits (e.g. demo3). Used to isolate pgvector rows per demo user folder.
    """
    if not path:
        return None
    norm = os.path.normpath(str(path)).replace("\\", "/")
    m = _DOCUMENTS_SCOPE.search(norm)
    if not m:
        return None
    segment = m.group(1)
    return segment if _VALID_DEMO_SCOPE.fullmatch(segment) else None


@lru_cache(maxsize=1)
def _face_tables_ready_marker() -> bool:
    """Cached only after ``create_db_and_tables`` succeeds."""
    create_db_and_tables()
    return True


def _ensure_face_tables() -> None:
    try:
        _face_tables_ready_marker()
    except Exception as exc:
        _face_tables_ready_marker.cache_clear()
        # Plugin import / task_schema registration must not require a live Postgres (e.g. CI).
        logger.warning(
            "Face embedding tables not ready (database unavailable): %s", exc
        )


def _scope_storage_key(demo_scope: str | None) -> str:
    return demo_scope or ""


def _vector_literal(vec: Any) -> str:
    if hasattr(vec, "tolist"):
        vec = vec.tolist()
    return "[" + ",".join(str(float(x)) for x in vec) + "]"


class _CollectionShim:
    """Minimal stand-in for tests/code that expect ``collection.name`` / ``str(collection)``."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name


class _FacematchPgClient:
    """Backward-compatible surface for ``DB.client.list_collections`` / ``delete_collection``."""

    def __init__(self, db: "Vector_Database"):
        self._db = db

    def list_collections(self) -> list[_CollectionShim]:
        return [_CollectionShim(n) for n in self._db.list_full_collection_names()]

    def delete_collection(self, name: str) -> None:
        self._db.delete_collection_by_full_name(name)


def get_vector_database(demo_scope: str | None = None) -> "Vector_Database":
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


def vector_db_for_current_request(path_hint: str | None = None) -> "Vector_Database":
    """
    Select face embedding store for the current HTTP request.

    When ``facematch_rescuebox_user_id`` is set (from ``X-RescueBox-User-Id``), use that user's
    isolated scope so collection lists and uploads match across find/bulk/delete flows.

    Otherwise use path-based ``.../Documents/demoN/...`` scope or the legacy default store.
    """
    uid = facematch_rescuebox_user_id.get()
    if uid:
        return get_vector_database(user_scope_from_rescuebox_user_id(uid))
    scope = facematch_demo_scope_from_path(path_hint) if path_hint else None
    return get_vector_database(scope)


def list_base_collection_names_for_schema(
    *,
    is_ensemble: bool = False,
    path_hint: str | None = None,
) -> list[str]:
    """Collection names for task-schema enums; empty when Postgres is unreachable."""
    try:
        db = vector_db_for_current_request(path_hint)
        return db.get_available_collections(isEnsemble=is_ensemble)
    except Exception as exc:
        logger.warning(
            "Could not list face-match collections for schema (database unavailable): %s",
            exc,
        )
        return []


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


class Vector_Database:
    def __init__(self, demo_scope: str | None = None):
        """
        Face embeddings in PostgreSQL/pgvector (``face_embeddings`` table), scoped by
        ``demo_scope`` (e.g. ``demo3`` or ``u_<hash>``) or legacy default when None.
        """
        if demo_scope is not None and not (
            _VALID_DEMO_SCOPE.fullmatch(demo_scope)
            or _VALID_USER_SCOPE.fullmatch(demo_scope)
        ):
            raise ValueError(f"Invalid facematch scope: {demo_scope!r}")
        self.demo_scope = demo_scope
        self.scope = _scope_storage_key(demo_scope)
        self.single_indicator = "S"
        self.ensemble_indicator = "E"
        _ensure_face_tables()
        self.client = _FacematchPgClient(self)

    def create_full_collection_name(self, base_name, detector, model, isEnsemble):
        return f"{base_name}_{detector.lower()[0:2]}{model.lower()[0:2]}{self.ensemble_indicator if isEnsemble else self.single_indicator}"

    def list_full_collection_names(self) -> list[str]:
        try:
            _ensure_face_tables()
            with Session(engine) as session:
                rows = session.exec(
                    select(FaceEmbedding.collection_name)
                    .where(FaceEmbedding.scope == self.scope)
                    .distinct()
                ).all()
            return sorted(set(rows))
        except Exception as exc:
            logger.warning(
                "Could not list face embedding collections for scope %r: %s",
                self.scope,
                exc,
            )
            return []

    def delete_collection_by_full_name(self, full_name: str) -> None:
        with Session(engine) as session:
            session.exec(
                delete(FaceEmbedding).where(
                    FaceEmbedding.scope == self.scope,
                    FaceEmbedding.collection_name == full_name,
                )
            )
            session.commit()

    def get_available_collections(self, isEnsemble=False):
        existing_collections = self.list_full_collection_names()
        indicator = self.ensemble_indicator if isEnsemble else self.single_indicator
        collections = list(
            filter(
                lambda name: name.split("_")[-1][-1] == indicator,
                existing_collections,
            )
        )
        collections = list(
            map(lambda name: "_".join(name.split("_")[:-1]), collections)
        )

        if isEnsemble:
            collections = list(set(collections))

        return collections

    def get_collection(self, collection: str):
        """Return full collection name (Chroma API compatibility)."""
        return collection

    def upload_embedding_to_database(self, data, collection):
        full_name = self.get_collection(collection)
        with Session(engine) as session:
            storage = FaceEmbeddingStorage(
                session, scope=self.scope, collection_name=full_name
            )
            for row in data:
                emb = row["embedding"]
                if hasattr(emb, "tolist"):
                    emb = emb.tolist()
                face_id = row["sha256_image"]
                image_path = row["image_path"]
                existing = session.exec(
                    select(FaceEmbedding).where(
                        FaceEmbedding.scope == self.scope,
                        FaceEmbedding.collection_name == full_name,
                        FaceEmbedding.face_id == face_id,
                    )
                ).first()
                if existing:
                    existing.image_path = image_path
                    existing.embedding = emb
                    session.add(existing)
                else:
                    storage.save_face(
                        face_id=face_id,
                        image_path=image_path,
                        embedding=emb,
                    )
            storage.commit()

    def _query_vectors(
        self,
        full_collection_name: str,
        query_vectors: Sequence[Any],
        n_results: int,
    ) -> list[dict]:
        rows_out: list[dict] = []
        with Session(engine) as session:
            for idx, qvec in enumerate(query_vectors):
                literal = _vector_literal(qvec)
                stmt = text(
                    """
                    SELECT face_id, image_path,
                           (embedding <=> CAST(:qvec AS vector)) AS distance
                    FROM face_embeddings
                    WHERE scope = :scope AND collection_name = :coll
                    ORDER BY embedding <=> CAST(:qvec AS vector)
                    LIMIT :limit
                    """
                )
                hits = session.execute(
                    stmt,
                    {
                        "qvec": literal,
                        "scope": self.scope,
                        "coll": full_collection_name,
                        "limit": n_results,
                    },
                ).fetchall()
                for hit in hits:
                    rows_out.append(
                        {
                            "query_index": idx,
                            "id": hit.face_id,
                            "distance": float(hit.distance),
                            "embedding": None,
                            "img_path": hit.image_path,
                        }
                    )
        return rows_out

    def query(self, collection, data, n_results, threshold):
        query_vectors = [image["embedding"] for image in data]
        full_name = self.get_collection(collection)
        flat = self._query_vectors(full_name, query_vectors, n_results)
        if not flat:
            return []

        result_df = pd.DataFrame(flat)
        result_df["similarity"] = 1 - result_df["distance"]

        if threshold is not None:
            result_df = result_df[result_df["similarity"] >= threshold]

        result_df = result_df.sort_values(
            by=["query_index", "similarity"], ascending=[True, False]
        )

        return result_df["img_path"].to_list()

    def query_bulk(self, collection, data, n_results, threshold, similarity_filter):
        full_name = self.get_collection(collection)
        data_rows: list[dict] = []

        with Session(engine) as session:
            for query_idx, query in enumerate(data):
                if not query:
                    data_rows.append(
                        {
                            "query_index": query_idx,
                            "face_idx": 0,
                            "id": None,
                            "distance": 1.0,
                            "embedding": None,
                            "img_path": None,
                        }
                    )
                    continue
                for face_idx, face in enumerate(query):
                    literal = _vector_literal(face["embedding"])
                    stmt = text(
                        """
                        SELECT face_id, image_path,
                               (embedding <=> CAST(:qvec AS vector)) AS distance
                        FROM face_embeddings
                        WHERE scope = :scope AND collection_name = :coll
                        ORDER BY embedding <=> CAST(:qvec AS vector)
                        LIMIT :limit
                        """
                    )
                    hits = session.execute(
                        stmt,
                        {
                            "qvec": literal,
                            "scope": self.scope,
                            "coll": full_name,
                            "limit": n_results,
                        },
                    ).fetchall()
                    if not hits:
                        data_rows.append(
                            {
                                "query_index": query_idx,
                                "face_idx": face_idx,
                                "id": None,
                                "distance": 1.0,
                                "embedding": None,
                                "img_path": None,
                            }
                        )
                        continue
                    for hit in hits:
                        data_rows.append(
                            {
                                "query_index": query_idx,
                                "face_idx": face_idx,
                                "id": hit.face_id,
                                "distance": float(hit.distance),
                                "embedding": None,
                                "img_path": hit.image_path,
                            }
                        )

        result_df = pd.DataFrame(data_rows)
        result_df["similarity"] = 1 - result_df["distance"]
        result_df = result_df.sort_values(
            by=["query_index", "face_idx", "similarity"], ascending=[True, True, False]
        )

        def filter_by_similarity(group):
            paths = group.loc[group["similarity"] >= threshold, "img_path"].tolist()
            return paths if paths else []

        def extract_paths(group):
            paths = group.loc[:, ["similarity", "img_path", "face_idx"]].to_dict(
                orient="records"
            )
            return paths if paths else []

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
