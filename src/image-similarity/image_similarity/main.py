from typing import TypedDict
import hashlib
import logging
import os
import threading

from pathlib import Path

import numpy as np
import onnxruntime as ort
import typer
from PIL import Image
from transformers import CLIPImageProcessor
from rb.lib.ml_service import MLService
from rb.api.models import (
    InputSchema,
    InputType,
    ParameterSchema,
    EnumParameterDescriptor,
    EnumVal,
    RangedIntParameterDescriptor,
    RangedFloatParameterDescriptor,
    IntRangeDescriptor,
    FloatRangeDescriptor,
    ResponseBody,
    TaskSchema,
    DirectoryInput,
    FileInput,
    BatchFileResponse,
    FileResponse,
    FileType,
)
from rb.api.database import ImageEmbedding, engine
from rb.api.embedding_storage import ImageEmbeddingStorage
from sqlmodel import Session, select
from sqlalchemy import bindparam, text, update


APP_NAME = "image_similarity"
logger = logging.getLogger(__name__)
logging.getLogger("filelock").setLevel(logging.WARNING)

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
_DEFAULT_MODEL = "openai/clip-vit-base-patch32"
_MODELS_DIR = Path(__file__).resolve().parent / "onnx_models"
_DEFAULT_ONNX_PATH = _MODELS_DIR / "clip-vit-base-patch32.onnx"
# Number of images fed to the ONNX session per GPU kernel launch.
# Larger values increase GPU utilisation; reduce if VRAM is limited.
_EMBED_BATCH_SIZE = 32

_EMBED_LOCKS_GUARD = threading.Lock()
_EMBED_LOCKS: dict[str, threading.Lock] = {}


def _lock_for_content_hash(content_sha256_hex: str) -> threading.Lock:
    with _EMBED_LOCKS_GUARD:
        lock = _EMBED_LOCKS.get(content_sha256_hex)
        if lock is None:
            lock = threading.Lock()
            _EMBED_LOCKS[content_sha256_hex] = lock
        return lock


class Inputs(TypedDict):
    input_dir: DirectoryInput
    query_image: FileInput


class Parameters(TypedDict):
    model_name: str
    top_k: int
    min_similarity: float


# ---------------------------------------------------------------------------
#  ONNX Runtime helpers  (same pattern as deepfake-detection / face-match)
# ---------------------------------------------------------------------------

def _get_ort_providers() -> list[str]:
    available = ort.get_available_providers()
    providers: list[str] = []
    if "CUDAExecutionProvider" in available:
        providers.append("CUDAExecutionProvider")
    if "CoreMLExecutionProvider" in available:
        providers.append("CoreMLExecutionProvider")
    providers.append("CPUExecutionProvider")
    return providers


def _load_onnx_vision_model() -> tuple[ort.InferenceSession, CLIPImageProcessor]:
    """Load the bundled CLIP vision ONNX model and image processor."""
    if not _DEFAULT_ONNX_PATH.exists():
        raise FileNotFoundError(
            f"ONNX model not found at {_DEFAULT_ONNX_PATH}. "
            "Download clip-vit-base-patch32.onnx into the onnx_models/ directory."
        )
    session = ort.InferenceSession(
        str(_DEFAULT_ONNX_PATH), providers=_get_ort_providers(),
    )
    processor = CLIPImageProcessor.from_pretrained(_DEFAULT_MODEL)
    return session, processor


def _supports_dynamic_batch(ort_session: ort.InferenceSession) -> bool:
    """Return True if the ONNX model accepts a variable batch dimension."""
    inp = ort_session.get_inputs()[0]
    batch_dim = inp.shape[0]
    return not isinstance(batch_dim, int) or batch_dim != 1


def _embed_images_batch(
    ort_session: ort.InferenceSession,
    processor: CLIPImageProcessor,
    image_paths: list[str],
    batch_size: int = _EMBED_BATCH_SIZE,
) -> dict[str, np.ndarray]:
    """Compute normalised embeddings for multiple images, batched when possible.

    If the ONNX model was exported with a dynamic batch axis, images are
    grouped into batches of ``batch_size`` and processed in a single forward
    pass per batch — this maximises GPU throughput.  If the model has a fixed
    batch dimension of 1 (common for default CLIP exports), we fall back to
    sequential processing but still vectorise the L2 normalisation across all
    results at the end.

    Returns a dict mapping each successfully processed path to its 1-D
    float32 embedding vector.
    """
    dynamic = _supports_dynamic_batch(ort_session)
    effective_batch = batch_size if dynamic else 1

    results: dict[str, np.ndarray] = {}
    for i in range(0, len(image_paths), effective_batch):
        batch_paths = image_paths[i : i + effective_batch]
        images: list[Image.Image] = []
        valid_paths: list[str] = []
        for p in batch_paths:
            try:
                images.append(Image.open(p).convert("RGB"))
                valid_paths.append(p)
            except Exception as exc:
                logger.warning("Could not open %s: %s", p, exc)
        if not images:
            continue
        pixel_values = processor(images=images, return_tensors="np")["pixel_values"].astype(
            np.float32
        )
        outputs = ort_session.run(None, {"pixel_values": pixel_values})
        embeds = outputs[0]  # (batch, embed_dim)
        embeds = embeds / np.linalg.norm(embeds, axis=-1, keepdims=True)
        for path, vec in zip(valid_paths, embeds):
            results[path] = vec
    return results


def _embed_image(
    ort_session: ort.InferenceSession,
    processor: CLIPImageProcessor,
    image_path: str,
) -> np.ndarray:
    """Compute a normalised embedding for a single image.  Returns a 1-D float32 array."""
    results = _embed_images_batch(ort_session, processor, [image_path])
    if image_path not in results:
        raise RuntimeError(f"Failed to embed {image_path}")
    return results[image_path]


# ---------------------------------------------------------------------------
#  Task schema
# ---------------------------------------------------------------------------

def task_schema() -> TaskSchema:
    model_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(key="openai/clip-vit-base-patch32", label="CLIP-ViT-B-32-OpenAI"),
        ],
        default="openai/clip-vit-base-patch32",
    )
    top_k_desc = RangedIntParameterDescriptor(
        range=IntRangeDescriptor(min=1, max=20),
        default=5,
    )
    min_similarity_desc = RangedFloatParameterDescriptor(
        range=FloatRangeDescriptor(min=0.0, max=1.0),
        default=0.5,
    )

    return TaskSchema(
        inputs=[
            InputSchema(
                key="input_dir",
                label="Directory of image files to search within",
                input_type=InputType.DIRECTORY,
            ),
            InputSchema(
                key="query_image",
                label="Query image — find visually similar images to this one",
                input_type=InputType.FILE,
            ),
        ],
        parameters=[
            ParameterSchema(
                key="model_name",
                label="CLIP model",
                subtitle="Model used to compute image embeddings for similarity comparison",
                value=model_enum,
            ),
            ParameterSchema(
                key="top_k",
                label="Top K results",
                subtitle="Number of most similar images to return",
                value=top_k_desc,
            ),
            ParameterSchema(
                key="min_similarity",
                label="Match threshold",
                subtitle="Similarity >= this counts as a match (image–image scores are typically higher than text–image)",
                value=min_similarity_desc,
            ),
        ],
    )


server = MLService(APP_NAME)
script_dir = os.path.dirname(os.path.abspath(__file__))
info_file_path = os.path.join(script_dir, "app-info.md")
with open(info_file_path, "r") as f:
    info = f.read()

server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Similar Image Search",
    author="UMass RescueLab",
    version="1.0.0",
    info=info,
    gpu=True,
)


def _paths_already_embedded(session: Session, paths: list[str]) -> set[str]:
    if not paths:
        return set()
    rows = session.exec(select(ImageEmbedding.path).where(ImageEmbedding.path.in_(paths))).all()
    return set(rows)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _embed_and_store_images(session, storage, file_paths, path_to_hash, ort_session, processor):
    """Ensure every path has an embedding row in ``image_embeddings``.  Returns paths ready for search.

    GPU optimisation: instead of calling the ONNX session once per image (N
    separate kernel launches), this function first identifies *all* paths that
    require a new embedding, deduplicates them by content hash, then feeds the
    whole set to ``_embed_images_batch`` so the GPU can process them in large
    batches.  Only after all embeddings are computed does it persist them.
    """
    already = _paths_already_embedded(session, file_paths)
    file_paths_set = set(file_paths)
    paths_for_search: list[str] = []
    newly_embedded = relocated = cloned = 0

    # Phase 1 — single DB pass to discover which content hashes already exist.
    hash_row_cache: dict[str, ImageEmbedding | None] = {}
    need_embed: list[str] = []  # paths whose content has no DB row at all
    for path in file_paths:
        if path in already:
            paths_for_search.append(path)
            continue
        h = path_to_hash[path]
        if h not in hash_row_cache:
            hash_row_cache[h] = session.exec(
                select(ImageEmbedding).where(ImageEmbedding.content_sha256 == h)
            ).first()
        if hash_row_cache[h] is None:
            need_embed.append(path)

    # Phase 2 — batch-embed all genuinely new content in one GPU pass.
    # Deduplicate by hash so identical files are only embedded once.
    batch_embeddings: dict[str, np.ndarray] = {}
    if need_embed:
        hash_to_rep: dict[str, str] = {}
        for p in need_embed:
            h = path_to_hash[p]
            if h not in hash_to_rep:
                hash_to_rep[h] = p
        unique_paths = list(hash_to_rep.values())
        logger.info("Batch-embedding %d new unique image(s) on GPU", len(unique_paths))
        raw = _embed_images_batch(ort_session, processor, unique_paths)
        for h, rep in hash_to_rep.items():
            if rep in raw:
                batch_embeddings[h] = raw[rep]

    # Phase 3 — persist / relocate / clone using the pre-computed embeddings.
    for path in file_paths:
        if path in already:
            continue
        h = path_to_hash[path]
        row = hash_row_cache.get(h)

        if row is None:
            with _lock_for_content_hash(h):
                # Re-check after acquiring the lock; a concurrent thread may
                # have inserted a row for the same content hash while we were
                # in the batch-embed step above.
                row = session.exec(
                    select(ImageEmbedding).where(ImageEmbedding.content_sha256 == h)
                ).first()
                if row is None:
                    if h in batch_embeddings:
                        try:
                            storage.save_embedding(
                                path, batch_embeddings[h].tolist(), content_sha256=h,
                            )
                            paths_for_search.append(path)
                            newly_embedded += 1
                            already.add(path)
                            session.flush()
                        except Exception as e:
                            logger.warning("Could not store embedding for %s: %s", path, e)
                    else:
                        logger.warning("Embedding not computed for %s — skipped", path)
                    continue

        if row is not None:
            if row.path == path:
                paths_for_search.append(path)
                already.add(path)
                session.flush()
                continue
            if row.path not in file_paths_set:
                session.execute(
                    update(ImageEmbedding).where(ImageEmbedding.id == row.id).values(path=path)
                )
                relocated += 1
                logger.info("Reused embedding by content hash (path updated): %s -> %s", row.path, path)
            else:
                emb = list(row.embedding) if row.embedding is not None else []
                session.add(ImageEmbedding(path=path, embedding=emb, content_sha256=h))
                cloned += 1
            paths_for_search.append(path)
            already.add(path)
            session.flush()
            continue

    if newly_embedded or relocated or cloned:
        storage.commit()

    return paths_for_search


def _cosine_similarity_search(
    query_vec: np.ndarray,
    session: Session,
    search_paths: list[str],
    top_k: int,
) -> list[dict]:
    """Find the top-K most similar embeddings using pgvector's cosine distance.

    Delegates to pgvector's indexed ``<=>`` operator so the DB can leverage
    HNSW/IVFFlat indexes and handle arbitrarily large candidate sets without
    loading all vectors into process memory.
    """
    if not search_paths:
        return []
    qvec_literal = "[" + ",".join(str(float(x)) for x in query_vec) + "]"
    stmt = (
        text(
            """
            SELECT id, path, 1 - (embedding <=> CAST(:qvec AS vector)) AS similarity
            FROM image_embeddings
            WHERE path IN :paths
            ORDER BY embedding <=> CAST(:qvec AS vector)
            LIMIT :top_k
            """
        ).bindparams(bindparam("paths", expanding=True))
    )
    rows = session.execute(
        stmt, {"qvec": qvec_literal, "paths": search_paths, "top_k": top_k},
    ).fetchall()
    return [
        {
            "id": row.id,
            "path": row.path,
            "similarity": round(float(row.similarity), 4),
        }
        for row in rows
    ]


def search_similar_images(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    """Find images visually similar to a query image inside ``input_dir``."""

    input_dir = str(inputs["input_dir"].path)
    query_image_path = str(inputs["query_image"].path)
    model_name = parameters.get("model_name", _DEFAULT_MODEL)
    top_k = int(parameters.get("top_k", 5))
    min_similarity = float(parameters.get("min_similarity", 0.5))

    ort_session, processor = _load_onnx_vision_model()
    logger.info(
        "ONNX vision model loaded: providers=%s model=%s",
        ort_session.get_providers(),
        model_name,
    )

    file_paths: list[str] = []
    for name in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, name)
        if os.path.isfile(path) and os.path.splitext(path)[1].lower() in ALLOWED_IMAGE_EXTS:
            file_paths.append(path)

    query_in_dir = query_image_path in set(file_paths)
    all_paths = file_paths if query_in_dir else file_paths + [query_image_path]

    path_to_hash: dict[str, str] = {}
    hashed_paths: list[str] = []
    for p in all_paths:
        try:
            path_to_hash[p] = _sha256_file(p)
            hashed_paths.append(p)
        except OSError as exc:
            logger.warning("Skip hashing %s: %s", p, exc)
    all_paths = hashed_paths

    with Session(engine) as session:
        storage = ImageEmbeddingStorage(session)
        paths_for_search = _embed_and_store_images(
            session, storage, all_paths, path_to_hash, ort_session, processor,
        )

        query_row = session.exec(
            select(ImageEmbedding).where(ImageEmbedding.path == query_image_path)
        ).first()

        if query_row is not None and query_row.embedding is not None:
            query_vec = np.array(list(query_row.embedding), dtype=np.float32)
        else:
            query_vec = _embed_image(ort_session, processor, query_image_path)

        search_paths = [p for p in paths_for_search if p != query_image_path]
        raw_results = _cosine_similarity_search(query_vec, session, search_paths, top_k)
        search_results = [
            {**hit, "is_match": hit["similarity"] >= min_similarity}
            for hit in raw_results
        ]

    query_label = f"Similar to {os.path.basename(query_image_path)}"
    file_responses: list[FileResponse] = []
    for rank, hit in enumerate(search_results, start=1):
        file_responses.append(
            FileResponse(
                file_type=FileType.IMG,
                path=str(hit["path"]),
                title=f"#{rank} · similarity {hit['similarity']}",
                subtitle=query_label,
                metadata={
                    "Query": query_label,
                    "Similarity": str(hit["similarity"]),
                    "Match": "Yes" if hit["is_match"] else "No",
                    "Model": model_name,
                    "id": str(hit.get("id", "")),
                },
            )
        )

    return ResponseBody(root=BatchFileResponse(files=file_responses))


def inputs_cli_parse(value: str) -> Inputs:
    if "|||" not in value:
        raise ValueError("Expected 'input_dir|||query_image_path' (use ||| between folder and query image).")
    dir_part, img_part = value.split("|||", 1)
    return Inputs(
        input_dir=DirectoryInput(path=dir_part.strip()),
        query_image=FileInput(path=img_part.strip()),
    )


def parameters_cli_parse(value: str) -> Parameters:
    parts = [p.strip() for p in value.split(",")]
    model_name = parts[0] if len(parts) > 0 and parts[0] else _DEFAULT_MODEL
    top_k = int(parts[1]) if len(parts) > 1 and parts[1] else 5
    min_similarity = float(parts[2]) if len(parts) > 2 and parts[2] else 0.5
    return Parameters(model_name=model_name, top_k=top_k, min_similarity=min_similarity)


server.add_ml_service(
    rule="/search_similar_images",
    ml_function=search_similar_images,
    inputs_cli_parser=typer.Argument(
        parser=inputs_cli_parse,
        help="Directory of images and query image as: input_dir|||query_image_path",
    ),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse,
        help="model_name,top_k,min_similarity",
    ),
    short_title="Find similar images (image query)",
    order=0,
    task_schema_func=task_schema,
)

app = server.app
if __name__ == "__main__":
    app()
