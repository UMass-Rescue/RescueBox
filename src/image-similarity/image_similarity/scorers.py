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
from sqlalchemy import bindparam, text
from sqlmodel import Session, select

from rb.api.database import ImageSimilarityEmbedding

logger = logging.getLogger(__name__)

_PDQ_BITS = 256


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
) -> list[dict]:
    """Find the top-K most similar embeddings using pgvector's cosine distance.

    Delegates to pgvector's indexed ``<=>`` operator so the DB can leverage
    HNSW/IVFFlat indexes and handle arbitrarily large candidate sets without
    loading all vectors into process memory.
    """
    if not search_paths:
        return []
    qvec_literal = "[" + ",".join(str(float(x)) for x in query_vec) + "]"
    stmt = text(
        """
            SELECT path,
                   1 - (embedding <=> CAST(:qvec AS vector)) AS score
            FROM image_similarity_embeddings
            WHERE path IN :paths AND model_name = :model_name
            ORDER BY embedding <=> CAST(:qvec AS vector)
            LIMIT :top_k
            """
    ).bindparams(bindparam("paths", expanding=True))
    rows = session.execute(
        stmt,
        {
            "qvec": qvec_literal,
            "paths": search_paths,
            "top_k": top_k,
            "model_name": model_name,
        },
    ).fetchall()
    return [{"path": r.path, "score": round(float(r.score), 4)} for r in rows]


def hamming_distance(hex_a: str, hex_b: str) -> int:
    """Compute the Hamming distance between two 64-char hex-encoded PDQ hashes."""
    return bin(int(hex_a, 16) ^ int(hex_b, 16)).count("1")


def pdq_similarity_search(
    session: Session,
    query_pdq: str,
    candidate_paths: list[str],
    top_k: int,
) -> list[dict]:
    """Rank candidates by PDQ Hamming similarity to the query hash."""
    if not candidate_paths or not query_pdq:
        return []

    rows = session.exec(
        select(ImageSimilarityEmbedding.path, ImageSimilarityEmbedding.pdq_hash).where(
            ImageSimilarityEmbedding.path.in_(candidate_paths),
            ImageSimilarityEmbedding.pdq_hash != "",
        )
    ).all()

    if not rows:
        logger.warning("pdq_similarity_search: no PDQ hashes found for candidates")
        return []

    scored = []
    for path, pdq_hash in rows:
        dist = hamming_distance(query_pdq, pdq_hash)
        scored.append({"path": path, "score": round(1.0 - dist / _PDQ_BITS, 4)})

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
    ) -> None:
        self._session = session
        self._query_vec = query_vec
        self._model_name = model_name

    def score(
        self, query_path: str, candidate_paths: list[str], top_k: int
    ) -> list[dict]:
        return cosine_similarity_search(
            self._session, self._query_vec, candidate_paths, top_k, self._model_name
        )


class PdqScorer:
    """Perceptual similarity scorer using Facebook's PDQ 256-bit hash.

    Similarity = 1 - (hamming_distance / 256).
    """

    def __init__(self, session: Session, query_pdq: str) -> None:
        self._session = session
        self._query_pdq = query_pdq

    def score(
        self, query_path: str, candidate_paths: list[str], top_k: int
    ) -> list[dict]:
        return pdq_similarity_search(
            self._session, self._query_pdq, candidate_paths, top_k
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
                p = hit["path"]
                path_raw[p] = path_raw.get(p, 0.0) + weight * hit["score"]
                path_weight[p] = path_weight.get(p, 0.0) + weight
                sub_scores.setdefault(p, {})[name] = hit["score"]

        combined = []
        for p, raw in path_raw.items():
            w = path_weight[p]
            entry: dict = {
                "path": p,
                "score": round(raw / w, 4) if w > 0 else 0.0,
            }
            for k, v in sub_scores.get(p, {}).items():
                entry[f"score_{k}"] = v
            combined.append(entry)

        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:top_k]
