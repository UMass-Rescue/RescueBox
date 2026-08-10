"""SQLAlchemy WHERE fragments for ``ImageSimilarityEmbedding`` (static-checker safe)."""

from __future__ import annotations

from typing import Any, cast

from rb.api.database import ImageSimilarityEmbedding, ImageSimilarityPrivateEmbedding

_cols = ImageSimilarityEmbedding.__table__.columns
_priv_cols = ImageSimilarityPrivateEmbedding.__table__.columns


def path_in(paths: list[str]):
    return cast(Any, _cols["path"]).in_(paths)


def path_eq(path: str):
    return cast(Any, _cols["path"]) == path


def model_name_eq(name: str):
    return cast(Any, _cols["model_name"]) == name


def pdq_hash_empty():
    return cast(Any, _cols["pdq_hash"]) == ""


def pdq_hash_nonempty():
    return cast(Any, _cols["pdq_hash"]) != ""


# Private table filters


def priv_path_in(paths: list[str]):
    return cast(Any, _priv_cols["path"]).in_(paths)


def priv_model_name_eq(name: str):
    return cast(Any, _priv_cols["model_name"]) == name


def priv_content_sha256_in(hashes: list[str]):
    return cast(Any, _priv_cols["content_sha256"]).in_(hashes)
