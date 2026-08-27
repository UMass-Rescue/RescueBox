"""
Scorer plugin interface and implementations for image-similarity search.

Each scorer produces a list of {"path": str, "score": float [0,1]} dicts ranked
by score descending.  The CombinedScorer merges multiple scorers via a weighted
average so that semantic and perceptual signals complement each other.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

import numpy as np
from rb.api.database import ImageSimilarityEmbedding, ImageSimilarityPrivateEmbedding
from image_similarity import sql_filters
from sqlalchemy import bindparam, text
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

_PDQ_BITS = 256
IMPORTED_EMBEDDING_PATH = "[imported]"


def _result_hit_key(path: str, row_id: int | None) -> str:
    if path == IMPORTED_EMBEDDING_PATH and row_id is not None:
        return f"{IMPORTED_EMBEDDING_PATH}#{row_id}"
    return path


def _search_hit(
    path: str,
    score: float,
    *,
    row_id: int | None = None,
    content_sha256: str = "",
    user_email: str = "",
    organization: str = "",
) -> dict:
    remote = path == IMPORTED_EMBEDDING_PATH
    hit: dict = {
        "path": path,
        "score": round(float(score), 4),
        "hit_key": _result_hit_key(path, row_id),
        "remote": remote,
    }
    if remote:
        hit["content_sha256"] = content_sha256
        hit["user_email"] = user_email
        hit["organization"] = organization
    return hit


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class ImageScorer(Protocol):
    """Minimal interface every scorer must satisfy."""

    def score(
        self,
        query_path: str,
        candidate_paths: list[str],
        top_k: int,
    ) -> list[dict]:
        """Return up to *top_k* results, each with 'path' and 'score' (0-1)."""
        ...


# ---------------------------------------------------------------------------
# Standalone search helpers (kept as plain functions for reuse / testability)
# ---------------------------------------------------------------------------


def cosine_similarity_search(
    session: Session,
    query_vec: np.ndarray,
    search_paths: list[str],
    top_k: int,
    model_name: str = "google/siglip2-so400m-patch14-384",
    use_private_table: bool = False,
    include_imported_private: bool = False,
) -> list[dict]:
    """Find the top-K most similar embeddings using pgvector's cosine distance.

    Delegates to pgvector's indexed ``<=>`` operator so the DB can leverage
    HNSW/IVFFlat indexes and handle arbitrarily large candidate sets without
    loading all vectors into process memory.
    """
    include_imported = use_private_table and include_imported_private
    if not search_paths and not include_imported:
        return []
    table = (
        "image_similarity_private_embeddings"
        if use_private_table
        else "image_similarity_embeddings"
    )
    qvec_literal = "[" + ",".join(str(float(x)) for x in query_vec) + "]"
    if include_imported:
        path_clause = (
            "(path IN :paths OR path = :imported_path)"
            if search_paths
            else "path = :imported_path"
        )
        stmt = text(
            f"""
            SELECT id, path, content_sha256, user_email, organization,
                   1 - (embedding <=> CAST(:qvec AS vector)) AS score
            FROM {table}
            WHERE model_name = :model_name
              AND {path_clause}
            ORDER BY embedding <=> CAST(:qvec AS vector)
            LIMIT :top_k
            """
        )
        if search_paths:
            stmt = stmt.bindparams(bindparam("paths", expanding=True))
        params: dict = {
            "qvec": qvec_literal,
            "top_k": top_k,
            "model_name": model_name,
            "imported_path": IMPORTED_EMBEDDING_PATH,
        }
        if search_paths:
            params["paths"] = search_paths
    else:
        stmt = text(
            f"""
            SELECT path,
                   1 - (embedding <=> CAST(:qvec AS vector)) AS score
            FROM {table}
            WHERE path IN :paths
              AND model_name = :model_name
            ORDER BY embedding <=> CAST(:qvec AS vector)
            LIMIT :top_k
            """
        ).bindparams(bindparam("paths", expanding=True))
        params = {
            "qvec": qvec_literal,
            "paths": search_paths,
            "top_k": top_k,
            "model_name": model_name,
        }
    rows = session.execute(stmt, params).fetchall()
    if include_imported:
        return [
            _search_hit(
                r.path,
                r.score,
                row_id=r.id,
                content_sha256=r.content_sha256 or "",
                user_email=r.user_email or "",
                organization=r.organization or "",
            )
            for r in rows
        ]
    return [_search_hit(r.path, r.score) for r in rows]


def hamming_distance(hex_a: str, hex_b: str) -> int:
    """Compute the Hamming distance between two 64-char hex-encoded PDQ hashes."""
    return bin(int(hex_a, 16) ^ int(hex_b, 16)).count("1")


def pdq_similarity_search(
    session: Session,
    query_pdq: str,
    candidate_paths: list[str],
    top_k: int,
    use_private_table: bool = False,
    include_imported_private: bool = False,
) -> list[dict]:
    """Rank candidates by PDQ Hamming similarity to the query hash."""
    include_imported = use_private_table and include_imported_private
    if not query_pdq or (not candidate_paths and not include_imported):
        return []

    if use_private_table:
        filters = [ImageSimilarityPrivateEmbedding.pdq_hash != ""]
        if candidate_paths and include_imported:
            filters.append(
                (sql_filters.priv_path_in(candidate_paths))
                | (ImageSimilarityPrivateEmbedding.path == IMPORTED_EMBEDDING_PATH)
            )
        elif candidate_paths:
            filters.append(sql_filters.priv_path_in(candidate_paths))
        else:
            filters.append(ImageSimilarityPrivateEmbedding.path == IMPORTED_EMBEDDING_PATH)
        rows = session.exec(
            select(
                ImageSimilarityPrivateEmbedding.id,
                ImageSimilarityPrivateEmbedding.path,
                ImageSimilarityPrivateEmbedding.pdq_hash,
                ImageSimilarityPrivateEmbedding.content_sha256,
                ImageSimilarityPrivateEmbedding.user_email,
                ImageSimilarityPrivateEmbedding.organization,
            ).where(*filters)
        ).all()
    else:
        rows = session.exec(
            select(
                ImageSimilarityEmbedding.path, ImageSimilarityEmbedding.pdq_hash
            ).where(
                sql_filters.path_in(candidate_paths),
                sql_filters.pdq_hash_nonempty(),
            )
        ).all()

    if not rows:
        logger.warning("pdq_similarity_search: no PDQ hashes found for candidates")
        return []

    scored = []
    for row in rows:
        if use_private_table:
            row_id, path, pdq_hash, content_sha256, user_email, organization = row
            dist = hamming_distance(query_pdq, pdq_hash)
            scored.append(
                _search_hit(
                    path,
                    1.0 - dist / _PDQ_BITS,
                    row_id=row_id,
                    content_sha256=content_sha256 or "",
                    user_email=user_email or "",
                    organization=organization or "",
                )
            )
        else:
            path, pdq_hash = row
            dist = hamming_distance(query_pdq, pdq_hash)
            scored.append(_search_hit(path, 1.0 - dist / _PDQ_BITS))

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Scorer classes (thin wrappers around the standalone helpers)
# ---------------------------------------------------------------------------


class ClipScorer:
    """Cosine-similarity scorer backed by the pgvector HNSW index."""

    def __init__(
        self,
        session: Session,
        query_vec: np.ndarray,
        model_name: str = "google/siglip2-so400m-patch14-384",
        use_private_table: bool = False,
        include_imported_private: bool = False,
    ) -> None:
        self._session = session
        self._query_vec = query_vec
        self._model_name = model_name
        self._use_private_table = use_private_table
        self._include_imported_private = include_imported_private

    def score(
        self, query_path: str, candidate_paths: list[str], top_k: int
    ) -> list[dict]:
        return cosine_similarity_search(
            self._session,
            self._query_vec,
            candidate_paths,
            top_k,
            self._model_name,
            self._use_private_table,
            self._include_imported_private,
        )


class PdqScorer:
    """Perceptual similarity scorer using Facebook's PDQ 256-bit hash.

    Similarity = 1 - (hamming_distance / 256).
    """

    def __init__(
        self,
        session: Session,
        query_pdq: str,
        use_private_table: bool = False,
        include_imported_private: bool = False,
    ) -> None:
        self._session = session
        self._query_pdq = query_pdq
        self._use_private_table = use_private_table
        self._include_imported_private = include_imported_private

    def score(
        self, query_path: str, candidate_paths: list[str], top_k: int
    ) -> list[dict]:
        return pdq_similarity_search(
            self._session,
            self._query_pdq,
            candidate_paths,
            top_k,
            self._use_private_table,
            self._include_imported_private,
        )


# ---------------------------------------------------------------------------
# Combined scorer
# ---------------------------------------------------------------------------


class CombinedScorer:
    """Merge multiple scorers via a weighted average.

    Each scorer is registered as a ``(name, scorer, weight)`` triple.
    If a path only appears in a subset of scorers (e.g. PDQ hash missing),
    the score is re-normalised over the scorers that *did* return it, so
    a missing hash doesn't silently halve the final score.
    """

    def __init__(self, scorers: list[tuple[str, ImageScorer, float]]) -> None:
        total = sum(w for _, _, w in scorers)
        if total == 0:
            raise ValueError("Sum of scorer weights must be > 0")
        self._scorers = [(name, s, w / total) for name, s, w in scorers]

    def score(
        self,
        query_path: str,
        candidate_paths: list[str],
        top_k: int,
    ) -> list[dict]:
        path_raw: dict[str, float] = {}
        path_weight: dict[str, float] = {}
        sub_scores: dict[str, dict[str, float]] = {}

        for name, scorer, weight in self._scorers:
            results = scorer.score(query_path, candidate_paths, len(candidate_paths))
            for hit in results:
                key = hit.get("hit_key", hit["path"])
                path_raw[key] = path_raw.get(key, 0.0) + weight * hit["score"]
                path_weight[key] = path_weight.get(key, 0.0) + weight
                sub_scores.setdefault(key, {})[name] = hit["score"]
                sub_scores[key]["_hit"] = hit

        combined = []
        for key, raw in path_raw.items():
            w = path_weight[key]
            base = sub_scores[key].pop("_hit", {"path": key, "score": 0.0})
            entry: dict = {
                **{k: v for k, v in base.items() if k != "score"},
                "path": base["path"],
                "score": round(raw / w, 4) if w > 0 else 0.0,
            }
            for k, v in sub_scores.get(key, {}).items():
                entry[f"score_{k}"] = v
            combined.append(entry)

        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:top_k]
