from typing import TypedDict
import hashlib
import logging
import os
import threading

from pathlib import Path

import numpy as np
import onnxruntime as ort
import pdqhash
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
from image_similarity.scorers import ClipScorer, CombinedScorer, PdqScorer
from sqlmodel import Session, select
from sqlalchemy import update


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
    scoring_mode: str


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


def _compute_pdq_hash(image_path: str) -> str:
    """Return the 64-char hex-encoded 256-bit PDQ perceptual hash for an image.

    PDQ (Facebook/Meta) is a robust perceptual hash that is invariant to minor
    crops, rotations, and compression artefacts.  Returns an empty string on
    failure so callers can treat missing hashes gracefully.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        img_array = np.array(img, dtype=np.uint8)
        hash_vector, _quality = pdqhash.compute(img_array)
        # hash_vector is a list of 256 ints (0 or 1); pack into bytes then hex.
        bits = 0
        for bit in hash_vector:
            bits = (bits << 1) | int(bit)
        return format(bits, "064x")
    except Exception as exc:
        logger.warning("PDQ hash failed for %s: %s", image_path, exc)
        return ""


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
    scoring_mode_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(key="combined", label="Combined (CLIP + PDQ)"),
            EnumVal(key="semantic", label="Semantic only (CLIP)"),
            EnumVal(key="pdq", label="Perceptual only (PDQ)"),
        ],
        default="combined",
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
            ParameterSchema(
                key="scoring_mode",
                label="Scoring mode",
                subtitle="Combined averages CLIP semantic cosine similarity and PDQ perceptual hash distance",
                value=scoring_mode_enum,
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


def _backfill_missing_pdq_hashes(session: Session, paths: list[str]) -> int:
    """Compute and store PDQ hashes for already-indexed images that lack one.

    Uses a single batch query instead of N individual lookups.
    """
    if not paths:
        return 0
    rows = session.exec(
        select(ImageEmbedding).where(
            ImageEmbedding.path.in_(paths),
            ImageEmbedding.pdq_hash == "",
        )
    ).all()
    filled = 0
    for row in rows:
        pdq = _compute_pdq_hash(row.path)
        if pdq:
            session.execute(
                update(ImageEmbedding)
                .where(ImageEmbedding.id == row.id)
                .values(pdq_hash=pdq)
            )
            filled += 1
    if filled:
        session.flush()
    return filled


def _discover_new_paths(session, file_paths, already, path_to_hash):
    """Return (hash_row_cache, need_embed) for paths not yet in the DB."""
    hash_row_cache: dict[str, ImageEmbedding | None] = {}
    need_embed: list[str] = []
    for path in file_paths:
        if path in already:
            continue
        h = path_to_hash[path]
        if h not in hash_row_cache:
            hash_row_cache[h] = session.exec(
                select(ImageEmbedding).where(ImageEmbedding.content_sha256 == h)
            ).first()
        if hash_row_cache[h] is None:
            need_embed.append(path)
    return hash_row_cache, need_embed


def _batch_embed_and_hash(need_embed, path_to_hash, ort_session, processor):
    """Batch-embed (CLIP) and batch-hash (PDQ) all genuinely new content.

    Deduplicates by content hash so identical files are processed only once.
    Returns (batch_embeddings, batch_pdq) keyed by content_sha256.
    """
    batch_embeddings: dict[str, np.ndarray] = {}
    batch_pdq: dict[str, str] = {}
    if not need_embed:
        return batch_embeddings, batch_pdq

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
        batch_pdq[h] = _compute_pdq_hash(rep)

    return batch_embeddings, batch_pdq


def _persist_new_path(
    path, h, row, batch_embeddings, batch_pdq, file_paths_set,
    session, storage, paths_for_search, already, counters,
):
    """Persist a single new path — insert, relocate, or clone."""
    if row is None:
        with _lock_for_content_hash(h):
            row = session.exec(
                select(ImageEmbedding).where(ImageEmbedding.content_sha256 == h)
            ).first()
            if row is None:
                if h in batch_embeddings:
                    try:
                        storage.save_embedding(
                            path, batch_embeddings[h].tolist(),
                            content_sha256=h,
                            pdq_hash=batch_pdq.get(h, ""),
                        )
                        paths_for_search.append(path)
                        counters["new"] += 1
                        already.add(path)
                        session.flush()
                    except Exception as e:
                        logger.warning("Could not store embedding for %s: %s", path, e)
                else:
                    logger.warning("Embedding not computed for %s — skipped", path)
                return

    if row is None:
        return

    if row.path == path:
        paths_for_search.append(path)
        already.add(path)
        return

    if row.path not in file_paths_set:
        update_vals: dict = {"path": path}
        if not row.pdq_hash:
            pdq = batch_pdq.get(h) or _compute_pdq_hash(path)
            if pdq:
                update_vals["pdq_hash"] = pdq
        session.execute(
            update(ImageEmbedding).where(ImageEmbedding.id == row.id).values(**update_vals)
        )
        counters["relocated"] += 1
        logger.info("Reused embedding by content hash (path updated): %s -> %s", row.path, path)
    else:
        emb = list(row.embedding) if row.embedding is not None else []
        pdq = row.pdq_hash or batch_pdq.get(h, "")
        session.add(ImageEmbedding(path=path, embedding=emb, content_sha256=h, pdq_hash=pdq))
        counters["cloned"] += 1

    paths_for_search.append(path)
    already.add(path)
    session.flush()


def _embed_and_store_images(session, storage, file_paths, path_to_hash, ort_session, processor):
    """Ensure every path has an embedding + PDQ row.  Returns paths ready for search."""
    already = _paths_already_embedded(session, file_paths)
    file_paths_set = set(file_paths)

    paths_for_search = [p for p in file_paths if p in already]
    _backfill_missing_pdq_hashes(session, paths_for_search)

    hash_row_cache, need_embed = _discover_new_paths(
        session, file_paths, already, path_to_hash,
    )
    batch_embeddings, batch_pdq = _batch_embed_and_hash(
        need_embed, path_to_hash, ort_session, processor,
    )

    counters = {"new": 0, "relocated": 0, "cloned": 0}
    for path in file_paths:
        if path in already:
            continue
        h = path_to_hash[path]
        _persist_new_path(
            path, h, hash_row_cache.get(h),
            batch_embeddings, batch_pdq, file_paths_set,
            session, storage, paths_for_search, already, counters,
        )

    if any(counters.values()):
        storage.commit()

    return paths_for_search


def search_similar_images(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    """Find images visually similar to a query image inside ``input_dir``."""

    input_dir = str(inputs["input_dir"].path)
    query_image_path = str(inputs["query_image"].path)
    model_name = parameters.get("model_name", _DEFAULT_MODEL)
    top_k = int(parameters.get("top_k", 5))
    min_similarity = float(parameters.get("min_similarity", 0.5))
    scoring_mode = parameters.get("scoring_mode", "combined")

    ort_session, processor = _load_onnx_vision_model()
    logger.info(
        "ONNX vision model loaded: providers=%s model=%s scoring_mode=%s",
        ort_session.get_providers(),
        model_name,
        scoring_mode,
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

        # Resolve query CLIP embedding (needed for semantic / combined).
        query_vec: np.ndarray | None = None
        if scoring_mode in ("semantic", "combined"):
            if query_row is not None and query_row.embedding is not None:
                query_vec = np.array(list(query_row.embedding), dtype=np.float32)
            else:
                query_vec = _embed_image(ort_session, processor, query_image_path)

        # Resolve query PDQ hash (needed for pdq / combined).
        query_pdq: str = ""
        if scoring_mode in ("pdq", "combined"):
            if query_row is not None and query_row.pdq_hash:
                query_pdq = query_row.pdq_hash
            else:
                query_pdq = _compute_pdq_hash(query_image_path)

        search_paths = [p for p in paths_for_search if p != query_image_path]

        if scoring_mode == "semantic":
            assert query_vec is not None
            scorer = ClipScorer(session, query_vec)
            raw_results = scorer.score(query_image_path, search_paths, top_k)
        elif scoring_mode == "pdq":
            scorer = PdqScorer(session, query_pdq)
            raw_results = scorer.score(query_image_path, search_paths, top_k)
        else:  # combined
            assert query_vec is not None
            clip_scorer = ClipScorer(session, query_vec)
            pdq_scorer = PdqScorer(session, query_pdq)
            scorer = CombinedScorer([
                ("clip", clip_scorer, 0.5),
                ("pdq", pdq_scorer, 0.5),
            ])
            raw_results = scorer.score(query_image_path, search_paths, top_k)

        search_results = [
            {**hit, "is_match": hit["score"] >= min_similarity}
            for hit in raw_results
        ]

    query_label = f"Similar to {os.path.basename(query_image_path)}"
    file_responses: list[FileResponse] = []
    for rank, hit in enumerate(search_results, start=1):
        score = hit["score"]
        meta: dict[str, str] = {
            "Query": query_label,
            "Similarity": str(score),
            "Match": "Yes" if hit["is_match"] else "No",
            "Scoring": scoring_mode,
            "Model": model_name,
        }
        if scoring_mode == "combined":
            if "score_clip" in hit:
                meta["CLIP score"] = str(hit["score_clip"])
            if "score_pdq" in hit:
                meta["PDQ score"] = str(hit["score_pdq"])
        file_responses.append(
            FileResponse(
                file_type=FileType.IMG,
                path=str(hit["path"]),
                title=f"#{rank} · similarity {score}",
                subtitle=query_label,
                metadata=meta,
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
    raw_mode = parts[3] if len(parts) > 3 and parts[3] else "combined"
    if raw_mode not in ("semantic", "pdq", "combined"):
        raise ValueError(f"scoring_mode must be one of semantic/pdq/combined, got: {raw_mode!r}")
    scoring_mode = raw_mode
    return Parameters(model_name=model_name, top_k=top_k, min_similarity=min_similarity, scoring_mode=scoring_mode)


server.add_ml_service(
    rule="/search_similar_images",
    ml_function=search_similar_images,
    inputs_cli_parser=typer.Argument(
        parser=inputs_cli_parse,
        help="Directory of images and query image as: input_dir|||query_image_path",
    ),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse,
        help="model_name,top_k,min_similarity,scoring_mode  (scoring_mode: combined|semantic|pdq)",
    ),
    short_title="Find similar images (image query)",
    order=0,
    task_schema_func=task_schema,
)

app = server.app
if __name__ == "__main__":
    app()
