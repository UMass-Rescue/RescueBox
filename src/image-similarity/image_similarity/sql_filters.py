"""SQLAlchemy WHERE fragments for ``ImageSimilarityEmbedding`` (static-checker safe)."""

from __future__ import annotations

from typing import Any, cast

from rb.api.database import ImageSimilarityEmbedding

_cols = ImageSimilarityEmbedding.__table__.columns


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
