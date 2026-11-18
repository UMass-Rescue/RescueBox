import hashlib
from collections.abc import Callable
from functools import partial

from image_matching.hashing.essay import ESSAY_MAX_WORDS, create_redacted_essay
from image_similarity.anonymizer import anonymize_image
from image_similarity.main import (
    _compute_pdq_hash,
    _embed_pil_image,
    _get_onnx_vision_model,
)
from PIL import Image
from rb.api.database import FileRecord

CHUNK_BYTES = 1024 * 1024

HASH_OPTIONS: dict[str, list[str]] = {
    "md5": ["md5"],
    "pdq": ["pdq"],
    "semantic": ["semantic", "private"],
    "essay": ["essay"],
}
COLUMNS: dict[str, str] = {
    "md5": "md5",
    "pdq": "pdq_hash",
    "semantic": "semantic_embedding",
    "private": "private_embedding",
    "essay": "essay",
}


def sha256_file(path: str) -> str:
    return _digest("sha256", path)


def md5_file(path: str) -> str:
    return _digest("md5", path)


def _digest(algorithm: str, path: str) -> str:
    digest = hashlib.new(algorithm)
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_embedding(path: str) -> list[float]:
    session, processor = _get_onnx_vision_model()
    image = Image.open(path).convert("RGB")
    return _embed_pil_image(session, processor, image).tolist()


def private_embedding(path: str) -> list[float]:
    session, processor = _get_onnx_vision_model()
    image = anonymize_image(Image.open(path).convert("RGB"))
    return _embed_pil_image(session, processor, image).tolist()


HASHERS: dict[str, Callable[[str], object]] = {
    "md5": md5_file,
    "pdq": _compute_pdq_hash,
    "semantic": semantic_embedding,
    "private": private_embedding,
    "essay": create_redacted_essay,
}


def _is_missing(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value)


def fill_missing(
    record: FileRecord,
    path: str,
    selected: list[str],
    max_essay_words: int = ESSAY_MAX_WORDS,
) -> int:
    """Compute only the selected hashes this file does not have yet."""
    hashers = {
        **HASHERS,
        "essay": partial(create_redacted_essay, max_words=max_essay_words),
    }
    computed = 0
    for name in selected:
        if _is_missing(getattr(record, COLUMNS[name])):
            setattr(record, COLUMNS[name], hashers[name](path))
            computed += 1
    return computed
