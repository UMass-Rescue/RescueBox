from typing import TypedDict
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pdqhash
import typer
from PIL import Image
from transformers import AutoImageProcessor
from rb.lib.job_progress import report_phased_file_progress
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
    TextParameterDescriptor,
    ResponseBody,
    TaskSchema,
    DirectoryInput,
    FileInput,
    BatchFileResponse,
    FileResponse,
    FileType,
)
from rb.api.database import (
    ImageSimilarityEmbedding,
    ImageSimilarityPrivateEmbedding,
    engine,
)
from rb.api.embedding_storage import (
    ImageSimilarityEmbeddingStorage,
    ImageSimilarityPrivateEmbeddingStorage,
)
from image_similarity.scorers import ClipScorer, CombinedScorer, ImageScorer, PdqScorer
from image_similarity.anonymizer import anonymize_image, DEFAULT_TARGET_LABELS
from image_similarity import sql_filters
from sqlmodel import Session, select


APP_NAME = "image_series_similarity"
logger = logging.getLogger(__name__)
logging.getLogger("filelock").setLevel(logging.WARNING)

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
_DEFAULT_MODEL = "google/siglip2-so400m-patch14-384"
_MODELS_DIR = Path(__file__).resolve().parent / "onnx_models"
_DEFAULT_ONNX_PATH = _MODELS_DIR / "siglip2-so400m-patch14-384.onnx"
# Number of images fed to the ONNX session per GPU kernel launch.
# Larger values increase GPU utilisation; reduce if VRAM is limited.
_EMBED_BATCH_SIZE = 32

_ORT_SESSION: ort.InferenceSession | None = None
_PROCESSOR: AutoImageProcessor | None = None


def _get_onnx_vision_model() -> tuple[ort.InferenceSession, AutoImageProcessor]:
    """Load the ONNX model once and cache it for the lifetime of the process."""
    global _ORT_SESSION, _PROCESSOR
    if _ORT_SESSION is None or _PROCESSOR is None:
        _ORT_SESSION, _PROCESSOR = _load_onnx_vision_model()
        logger.info("ONNX vision model loaded and cached.")
    return _ORT_SESSION, _PROCESSOR


class Inputs(TypedDict):
    input_dir: DirectoryInput
    query_image: FileInput


class Parameters(TypedDict):
    user_email: str
    enable_anonymized: str
    model_name: str
    top_k: int
    min_similarity: float
    scoring_mode: str


class ExportInputs(TypedDict):
    output_dir: DirectoryInput


class ExportParameters(TypedDict):
    user_email: str


class ImportInputs(TypedDict):
    input_file: FileInput


class ImportParameters(TypedDict):
    user_email: str


# ---------------------------------------------------------------------------
#  ONNX Runtime helpers  (same pattern as deepfake-detection / face-match)
# ---------------------------------------------------------------------------


def _get_ort_providers() -> list[str]:
    available = ort.get_available_providers()
    providers: list[str] = []
    if "CUDAExecutionProvider" in available:
        providers.append("CUDAExecutionProvider")
    # Skip CoreML - causes errors with CLIP models on macOS
    # if "CoreMLExecutionProvider" in available:
    #     providers.append("CoreMLExecutionProvider")
    providers.append("CPUExecutionProvider")
    return providers


def _load_onnx_vision_model() -> tuple[ort.InferenceSession, AutoImageProcessor]:
    """Load the bundled vision ONNX model and its image processor."""
    if not _DEFAULT_ONNX_PATH.exists():
        raise FileNotFoundError(
            f"ONNX model not found at {_DEFAULT_ONNX_PATH}. "
            f"Download the vision ONNX export of {_DEFAULT_MODEL} into the onnx_models/ directory."
        )
    session = ort.InferenceSession(
        str(_DEFAULT_ONNX_PATH),
        providers=_get_ort_providers(),
    )
    processor = AutoImageProcessor.from_pretrained(_MODELS_DIR)
    return session, processor


def _supports_dynamic_batch(ort_session: ort.InferenceSession) -> bool:
    """Return True if the ONNX model accepts a variable batch dimension."""
    inp = ort_session.get_inputs()[0]
    batch_dim = inp.shape[0]
    return not isinstance(batch_dim, int) or batch_dim != 1


def _embed_images_batch(
    ort_session: ort.InferenceSession,
    processor: AutoImageProcessor,
    image_paths: list[str],
    batch_size: int = _EMBED_BATCH_SIZE,
    enable_anonymized: bool = False,
) -> tuple[dict[str, np.ndarray], int]:
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
    total = len(image_paths)
    processed = 0
    last_reported = 0

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
        pixel_values = processor(images=images, return_tensors="np")[
            "pixel_values"
        ].astype(np.float32)
        outputs = ort_session.run(["pooler_output"], {"pixel_values": pixel_values})
        embeds = outputs[0]
        embeds = embeds / np.linalg.norm(embeds, axis=-1, keepdims=True)
        for path, vec in zip(valid_paths, embeds):
            results[path] = vec
        processed += len(valid_paths)
        if enable_anonymized:
            last_reported = report_phased_file_progress(
                None, 1, 3, processed, total, last_reported
            )
        else:
            last_reported = report_phased_file_progress(
                None, 1, 2, processed, total, last_reported
            )
    if total > 0:
        if enable_anonymized:
            last_reported = report_phased_file_progress(
                None, 1, 3, total, total, last_reported
            )
        else:
            last_reported = report_phased_file_progress(
                None, 1, 2, total, total, last_reported
            )
    return results, last_reported


def _embed_pil_image(
    ort_session: ort.InferenceSession,
    processor: AutoImageProcessor,
    image: Image.Image,
) -> np.ndarray:
    """Compute a normalised embedding from an in-memory PIL Image via ONNX Runtime."""
    pixel_values = processor(images=image, return_tensors="np")["pixel_values"].astype(
        np.float32
    )
    outputs = ort_session.run(["pooler_output"], {"pixel_values": pixel_values})
    embeds = outputs[0]
    embeds = embeds / np.linalg.norm(embeds, axis=-1, keepdims=True)
    return embeds.squeeze()


_PDQ_HEX_LEN = 64  # 256 bits = 64 hex chars


def _compute_pdq_hash(source: Image.Image | str) -> str:
    """Compute a 64-char hex PDQ hash from a PIL Image or file path."""
    try:
        img = (
            Image.open(source).convert("RGB")
            if isinstance(source, str)
            else source.convert("RGB")
        )
        hash_vector, _quality = pdqhash.compute(np.array(img, dtype=np.uint8))
        bits = 0
        for bit in hash_vector:
            bits = (bits << 1) | int(bit)
        hex_hash = format(bits, "064x")
        if len(hex_hash) != _PDQ_HEX_LEN:
            logger.warning("PDQ hash length mismatch: got %d chars", len(hex_hash))
            return ""
        return hex_hash
    except Exception as exc:
        logger.warning(
            "PDQ hash failed for %s: %s",
            source if isinstance(source, str) else "image",
            exc,
        )
        return ""


# ---------------------------------------------------------------------------
#  Task schema
# ---------------------------------------------------------------------------


def task_schema() -> TaskSchema:
    model_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(key="google/siglip2-so400m-patch14-384", label="SigLIP2-SO400M"),
        ],
        default="google/siglip2-so400m-patch14-384",
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

    email_desc = TextParameterDescriptor(default="")
    anonymize_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(key="no", label="No"),
            EnumVal(key="yes", label="Yes"),
        ],
        default="no",
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
                label="Query image — find images from the same series as this one",
                input_type=InputType.FILE,
            ),
        ],
        parameters=[
            ParameterSchema(
                key="user_email",
                label="Your email",
                subtitle="Required — identifies embedding ownership for cross-agency sharing",
                value=email_desc,
            ),
            ParameterSchema(
                key="enable_anonymized",
                label="Create anonymized embeddings",
                subtitle="Blacks out faces, text and logos before embedding so raw image content is never shared across agencies",
                value=anonymize_enum,
            ),
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


def export_task_schema() -> TaskSchema:
    email_desc = TextParameterDescriptor(default="")
    return TaskSchema(
        inputs=[
            InputSchema(
                key="output_dir",
                label="Output directory",
                input_type=InputType.DIRECTORY,
            ),
        ],
        parameters=[
            ParameterSchema(
                key="user_email",
                label="Filter by email (optional)",
                subtitle="Leave empty to export all private embeddings, or enter an email to export only that user's embeddings",
                value=email_desc,
            ),
        ],
    )


def import_task_schema() -> TaskSchema:
    email_desc = TextParameterDescriptor(default="")
    return TaskSchema(
        inputs=[
            InputSchema(
                key="input_file",
                label="Embeddings file (.json)",
                input_type=InputType.FILE,
            ),
        ],
        parameters=[
            ParameterSchema(
                key="user_email",
                label="Your email",
                subtitle="Required — identifies who is importing these embeddings (for audit)",
                value=email_desc,
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
    name="Image Series Similarity",
    author="UMass RescueLab",
    version="1.0.0",
    info=info,
    gpu=True,
)


def _paths_already_embedded(
    session: Session, paths: list[str], model_name: str = _DEFAULT_MODEL
) -> set[str]:
    if not paths:
        return set()
    rows = session.exec(
        select(ImageSimilarityEmbedding.path).where(
            sql_filters.path_in(paths),
            sql_filters.model_name_eq(model_name),
        )
    ).all()
    return set(rows)


_SHA256_HEX_LEN = 64  # SHA-256 = 32 bytes = 64 hex chars


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    digest = h.hexdigest()
    assert len(digest) == _SHA256_HEX_LEN
    return digest


def _discover_new_paths(
    session: Session,
    file_paths: list[str],
    already: set[str],
    path_to_hash: dict[str, str],
    model_name: str = _DEFAULT_MODEL,
):
    """Return (hash_row_cache, need_embed) for paths not yet in the DB."""
    hash_row_cache: dict[str, ImageSimilarityEmbedding | None] = {}
    need_embed: list[str] = []
    for path in file_paths:
        if path in already:
            continue
        h = path_to_hash[path]
        if h not in hash_row_cache:
            hash_row_cache[h] = session.exec(
                select(ImageSimilarityEmbedding).where(
                    ImageSimilarityEmbedding.content_sha256 == h,
                    ImageSimilarityEmbedding.model_name == model_name,
                )
            ).first()
        if hash_row_cache[h] is None:
            need_embed.append(path)
    return hash_row_cache, need_embed


def _batch_embed_and_hash(
    need_embed: list[str],
    path_to_hash: dict[str, str],
    ort_session: ort.InferenceSession,
    processor: AutoImageProcessor,
    enable_anonymized: bool = False,
) -> tuple[dict[str, np.ndarray], dict[str, str], int]:
    """Batch-embed (CLIP) and batch-hash (PDQ) all genuinely new content.

    Deduplicates by content hash so identical files are processed only once.
    Returns (batch_embeddings, batch_pdq) keyed by content_sha256.
    """
    batch_embeddings: dict[str, np.ndarray] = {}
    batch_pdq: dict[str, str] = {}
    if not need_embed:
        return batch_embeddings, batch_pdq, 0

    hash_to_rep: dict[str, str] = {}
    for p in need_embed:
        h = path_to_hash[p]
        if h not in hash_to_rep:
            hash_to_rep[h] = p
    unique_paths = list(hash_to_rep.values())

    logger.info("Batch-embedding %d new unique image(s) on GPU", len(unique_paths))
    raw, last_reported = _embed_images_batch(
        ort_session, processor, unique_paths, enable_anonymized=enable_anonymized
    )
    processed = 0
    total = len(hash_to_rep)
    for h, rep in hash_to_rep.items():
        if rep in raw:
            batch_embeddings[h] = raw[rep]
        batch_pdq[h] = _compute_pdq_hash(rep)
        processed += 1
        if enable_anonymized and total > 0:
            last_reported = report_phased_file_progress(
                None, 2, 3, processed, total, last_reported
            )
        else:
            last_reported = report_phased_file_progress(
                None, 2, 2, processed, total, last_reported
            )

    return batch_embeddings, batch_pdq, last_reported


def _persist_new_path(
    path: str,
    h: str,
    row: ImageSimilarityEmbedding | None,
    batch_embeddings: dict[str, np.ndarray],
    batch_pdq: dict[str, str],
    file_paths_set: set[str],
    session: Session,
    storage: ImageSimilarityEmbeddingStorage,
    paths_for_search: list[str],
    already: set[str],
    counters: dict[str, int],
    model_name: str = _DEFAULT_MODEL,
):
    """Persist a single new path — insert, relocate, or clone."""
    if row is None:
        row = session.exec(
            select(ImageSimilarityEmbedding).where(
                ImageSimilarityEmbedding.content_sha256 == h,
                ImageSimilarityEmbedding.model_name == model_name,
            )
        ).first()
        if row is None:
            if h in batch_embeddings:
                try:
                    storage.save_embedding(
                        path,
                        batch_embeddings[h].tolist(),
                        content_sha256=h,
                        pdq_hash=batch_pdq[h],
                    )
                    paths_for_search.append(path)
                    counters["new"] += 1
                    already.add(path)
                    session.flush()
                except Exception as e:
                    session.rollback()
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
        row.path = path
        counters["relocated"] += 1
        logger.info(
            "Reused embedding by content hash (path updated): %s -> %s", row.path, path
        )
    else:
        emb = list(row.embedding) if row.embedding is not None else []
        session.add(
            ImageSimilarityEmbedding(
                path=path,
                embedding=emb,
                content_sha256=h,
                pdq_hash=row.pdq_hash,
            )
        )
        counters["cloned"] += 1

    paths_for_search.append(path)
    already.add(path)
    session.flush()


def _embed_and_store_images(
    session: Session,
    storage: ImageSimilarityEmbeddingStorage,
    file_paths: list[str],
    path_to_hash: dict[str, str],
    ort_session: ort.InferenceSession,
    processor: AutoImageProcessor,
    model_name: str = _DEFAULT_MODEL,
    enable_anonymized: bool = False,
) -> tuple[list[str], int]:
    """Ensure every path has an embedding + PDQ row.  Returns paths ready for search."""
    already = _paths_already_embedded(session, file_paths, model_name)
    file_paths_set = set(file_paths)

    paths_for_search = [p for p in file_paths if p in already]

    hash_row_cache, need_embed = _discover_new_paths(
        session,
        file_paths,
        already,
        path_to_hash,
        model_name,
    )
    batch_embeddings, batch_pdq, last_reported = _batch_embed_and_hash(
        need_embed,
        path_to_hash,
        ort_session,
        processor,
        enable_anonymized=enable_anonymized,
    )

    counters = {"new": 0, "relocated": 0, "cloned": 0}
    for path in file_paths:
        if path in already:
            continue
        h = path_to_hash[path]
        _persist_new_path(
            path,
            h,
            hash_row_cache.get(h),
            batch_embeddings,
            batch_pdq,
            file_paths_set,
            session,
            storage,
            paths_for_search,
            already,
            counters,
            model_name,
        )

    if any(counters.values()):
        storage.commit()

    return paths_for_search, last_reported


def _collect_image_paths(input_dir: str) -> list[str]:
    """Return sorted list of valid image file paths from a directory."""
    paths: list[str] = []
    for name in sorted(os.listdir(input_dir)):
        if os.path.splitext(name)[1].lower() not in ALLOWED_IMAGE_EXTS:
            continue
        full = os.path.join(input_dir, name)
        if os.path.isfile(full):
            paths.append(full)
    return paths


def _hash_paths(paths: list[str]) -> tuple[list[str], dict[str, str]]:
    """SHA-256 hash each path. Returns (valid_paths, path_to_hash)."""
    path_to_hash: dict[str, str] = {}
    valid: list[str] = []
    for p in paths:
        try:
            path_to_hash[p] = _sha256_file(p)
            valid.append(p)
        except OSError as exc:
            logger.warning("Skip hashing %s: %s", p, exc)
    return valid, path_to_hash


def _load_query_image(query_image_path: str, anonymize: bool) -> Image.Image:
    """Open query image, applying CLIPSeg anonymization when requested."""
    img = Image.open(query_image_path).convert("RGB")
    if anonymize:
        return anonymize_image(img)
    return img


def _build_scorer(
    session: Session,
    scoring_mode: str,
    query_row: ImageSimilarityEmbedding | ImageSimilarityPrivateEmbedding | None,
    query_image_path: str,
    model_name: str,
    ort_session: ort.InferenceSession,
    processor: AutoImageProcessor,
    use_private_table: bool = False,
) -> ImageScorer:
    """Build a scorer that ranks candidates against the query image."""
    has_vec = query_row is not None and query_row.embedding is not None
    needs_pdq_from_image = scoring_mode in ("pdq", "combined") and query_row is None
    needs_image = (
        scoring_mode in ("semantic", "combined") and not has_vec
    ) or needs_pdq_from_image

    query_img = (
        _load_query_image(query_image_path, use_private_table) if needs_image else None
    )

    query_vec: np.ndarray | None = None
    if scoring_mode in ("semantic", "combined"):
        if has_vec:
            query_vec = np.array(list(query_row.embedding), dtype=np.float32)
        else:
            query_vec = _embed_pil_image(ort_session, processor, query_img)

    query_pdq = ""
    if scoring_mode in ("pdq", "combined"):
        if query_row is not None:
            query_pdq = query_row.pdq_hash
        else:
            query_pdq = _compute_pdq_hash(query_img)

    if scoring_mode == "semantic":
        return ClipScorer(
            session, query_vec, model_name, use_private_table=use_private_table
        )
    if scoring_mode == "pdq":
        return PdqScorer(session, query_pdq, use_private_table=use_private_table)

    return CombinedScorer(
        [
            (
                "clip",
                ClipScorer(
                    session, query_vec, model_name, use_private_table=use_private_table
                ),
                0.6,
            ),
            (
                "pdq",
                PdqScorer(session, query_pdq, use_private_table=use_private_table),
                0.4,
            ),
        ]
    )


def _build_metadata(
    hit: dict,
    scoring_mode: str,
    model_name: str,
    query_name: str,
) -> dict[str, str]:
    """Build per-result metadata dict with consistent columns across all modes."""
    scoring_labels = {
        "combined": "Combined (CLIP + PDQ)",
        "semantic": "Semantic only (CLIP)",
        "pdq": "Perceptual only (PDQ)",
    }
    meta: dict[str, str] = {
        "Scoring Mode": scoring_labels.get(scoring_mode, scoring_mode),
        "Match": "Yes" if hit["is_match"] else "No",
    }
    if scoring_mode in ("semantic", "combined"):
        meta["CLIP Model"] = model_name
    meta["Query"] = f"Series match for {query_name}"
    return meta


def _privacy_protocol_tag(labels: list[str]) -> str:
    """Encode anonymization config into a single cache-key string."""
    return "clipseg-blackout-v1:" + ",".join(sorted(labels))


def _uncached_private_paths(
    session: Session,
    file_paths: list[str],
    path_to_hash: dict[str, str],
    model_name: str,
    protocol: str,
) -> list[str]:
    """Return paths whose content hash has no private embedding yet."""
    hashes = [path_to_hash[p] for p in file_paths if p in path_to_hash]
    if not hashes:
        return []
    cached = set(
        session.exec(
            select(ImageSimilarityPrivateEmbedding.content_sha256).where(
                sql_filters.priv_content_sha256_in(hashes),
                sql_filters.priv_model_name_eq(model_name),
                ImageSimilarityPrivateEmbedding.privacy_protocol == protocol,
            )
        ).all()
    )
    return [p for p in file_paths if path_to_hash.get(p) not in cached]


def _group_by_hash(
    paths: list[str], path_to_hash: dict[str, str]
) -> dict[str, list[str]]:
    """Group paths by content hash for deduplication."""
    groups: dict[str, list[str]] = {}
    for p in paths:
        h = path_to_hash.get(p, "")
        if h:
            groups.setdefault(h, []).append(p)
    return groups


def _create_private_embeddings(
    session: Session,
    file_paths: list[str],
    path_to_hash: dict[str, str],
    ort_session: ort.InferenceSession,
    processor: AutoImageProcessor,
    user_email: str,
    model_name: str = _DEFAULT_MODEL,
    last_reported: int = 0,
) -> str:
    """Anonymize images via CLIPSeg and store private embeddings + PDQ hashes."""
    protocol = _privacy_protocol_tag(list(DEFAULT_TARGET_LABELS))
    new_paths = _uncached_private_paths(
        session,
        file_paths,
        path_to_hash,
        model_name,
        protocol,
    )
    if not new_paths:
        logger.info("Private embeddings: all %d paths already cached", len(file_paths))
        return protocol

    storage = ImageSimilarityPrivateEmbeddingStorage(
        session,
        model_name=model_name,
        user_email=user_email,
        privacy_protocol=protocol,
    )
    groups = _group_by_hash(new_paths, path_to_hash)
    total = len(groups)

    embedded, cloned = 0, 0
    failures: list[tuple[str, str]] = []
    for h, paths in groups.items():
        try:
            img = Image.open(paths[0]).convert("RGB")
            anonymized = anonymize_image(img)
            emb = _embed_pil_image(ort_session, processor, anonymized).tolist()
            pdq_hash = _compute_pdq_hash(anonymized)
            for path in paths:
                storage.save_embedding(path, emb, content_sha256=h, pdq_hash=pdq_hash)
            embedded += 1
            cloned += len(paths) - 1
            session.flush()
            last_reported = report_phased_file_progress(
                None, 3, 3, embedded, total, last_reported
            )
        except Exception as exc:
            failures.append((paths[0], str(exc)))
            logger.warning("Private embedding failed for %s: %s", paths[0], exc)

    if embedded or cloned:
        storage.commit()
    logger.info(
        "Private embeddings (%s): %d unique + %d cloned (skipped %d cached, %d failed)",
        protocol,
        embedded,
        cloned,
        len(file_paths) - len(new_paths),
        len(failures),
    )
    if embedded == 0 and failures:
        raise RuntimeError(
            f"All {len(failures)} private embeddings failed. "
            f"First error: {failures[0][1]}"
        )
    return protocol


# ---------------------------------------------------------------------------
#  Export / Import routes
# ---------------------------------------------------------------------------

_EXPORT_FORMAT_VERSION = 1


def export_embeddings(
    inputs: ExportInputs, parameters: ExportParameters
) -> ResponseBody:
    """Export private embeddings to a JSONL file for cross-machine sharing."""
    output_dir = os.path.realpath(str(inputs["output_dir"].path))
    filter_email = parameters.get("user_email", "").strip()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"private_embeddings_{timestamp}.json"
    output_path = os.path.join(output_dir, filename)

    with Session(engine) as session:
        query = select(ImageSimilarityPrivateEmbedding)
        if filter_email:
            query = query.where(
                ImageSimilarityPrivateEmbedding.user_email == filter_email
            )
        rows = session.exec(query).all()

        if not rows:
            raise ValueError(
                "No private embeddings found"
                + (f" for email {filter_email}" if filter_email else "")
                + ". Run a search with 'Create anonymized embeddings' enabled first."
            )

        with open(output_path, "w") as f:
            header = {
                "format_version": _EXPORT_FORMAT_VERSION,
                "export_date": datetime.now(timezone.utc).isoformat(),
                "source_email": filter_email or "(all)",
                "count": len(rows),
            }
            f.write(json.dumps(header) + "\n")

            for row in rows:
                record = {
                    "content_sha256": row.content_sha256,
                    "embedding": list(row.embedding) if row.embedding else [],
                    "pdq_hash": row.pdq_hash,
                    "user_email": row.user_email,
                    "privacy_protocol": row.privacy_protocol,
                    "model_name": row.model_name,
                }
                f.write(json.dumps(record) + "\n")

    logger.info("Exported %d private embeddings to %s", len(rows), output_path)

    return ResponseBody(
        root=BatchFileResponse(
            files=[
                FileResponse(
                    file_type=FileType.TEXT,
                    path=output_path,
                    title=f"Exported {len(rows)} private embeddings",
                    metadata={
                        "Format": "JSONL",
                        "Count": str(len(rows)),
                        "Filter": filter_email or "(all users)",
                    },
                )
            ]
        )
    )


def import_embeddings(
    inputs: ImportInputs, parameters: ImportParameters
) -> ResponseBody:
    """Import private embeddings from a JSONL file."""
    input_path = os.path.realpath(str(inputs["input_file"].path))
    importer_email = parameters.get("user_email", "").strip()

    if not importer_email:
        raise ValueError("user_email is required to track who imported these embeddings.")

    imported = 0
    skipped = 0
    errors: list[str] = []

    with Session(engine) as session:
        with open(input_path, "r") as f:
            header_line = f.readline()
            try:
                header = json.loads(header_line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL header: {e}") from e

            version = header.get("format_version", 0)
            if version != _EXPORT_FORMAT_VERSION:
                raise ValueError(
                    f"Unsupported format version {version}, expected {_EXPORT_FORMAT_VERSION}"
                )

            for line_num, line in enumerate(f, start=2):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: invalid JSON - {e}")
                    continue

                content_sha256 = record.get("content_sha256", "")
                privacy_protocol = record.get("privacy_protocol", "")
                model_name = record.get("model_name", _DEFAULT_MODEL)

                if not content_sha256 or not privacy_protocol:
                    errors.append(f"Line {line_num}: missing content_sha256 or privacy_protocol")
                    continue

                existing = session.exec(
                    select(ImageSimilarityPrivateEmbedding).where(
                        ImageSimilarityPrivateEmbedding.content_sha256 == content_sha256,
                        ImageSimilarityPrivateEmbedding.privacy_protocol == privacy_protocol,
                        ImageSimilarityPrivateEmbedding.model_name == model_name,
                    )
                ).first()

                if existing:
                    skipped += 1
                    continue

                embedding = record.get("embedding", [])
                new_row = ImageSimilarityPrivateEmbedding(
                    path="[imported]",
                    content_sha256=content_sha256,
                    model_name=model_name,
                    embedding=embedding,
                    pdq_hash=record.get("pdq_hash", ""),
                    user_email=record.get("user_email", ""),
                    privacy_protocol=privacy_protocol,
                )
                session.add(new_row)
                imported += 1

        session.commit()

    logger.info(
        "Import complete: %d imported, %d skipped (duplicates), %d errors",
        imported,
        skipped,
        len(errors),
    )

    error_summary = f"; {len(errors)} errors" if errors else ""
    return ResponseBody(
        root=BatchFileResponse(
            files=[
                FileResponse(
                    file_type=FileType.TEXT,
                    path=input_path,
                    title=f"Imported {imported} embeddings ({skipped} skipped){error_summary}",
                    metadata={
                        "Imported": str(imported),
                        "Skipped (duplicates)": str(skipped),
                        "Errors": str(len(errors)),
                        "Importer": importer_email,
                    },
                )
            ]
        )
    )


def search_series(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    """Find images from the same series as a query image inside ``input_dir``."""

    input_dir = os.path.realpath(str(inputs["input_dir"].path))
    query_image_path = os.path.realpath(str(inputs["query_image"].path))
    model_name = parameters.get("model_name", _DEFAULT_MODEL)
    top_k = int(parameters.get("top_k", 5))
    min_similarity = float(parameters.get("min_similarity", 0.5))
    scoring_mode = parameters.get("scoring_mode", "combined")
    user_email = parameters.get("user_email", "").strip()
    enable_anonymized = parameters.get("enable_anonymized", "no") == "yes"
    if not user_email:
        raise ValueError("user_email is required for embedding ownership attribution.")

    ort_session, processor = _get_onnx_vision_model()
    logger.info(
        "Scoring: providers=%s model=%s mode=%s email=%s",
        ort_session.get_providers(),
        model_name,
        scoring_mode,
        user_email or "(not provided)",
    )

    file_paths = _collect_image_paths(input_dir)
    all_paths = (
        file_paths
        if query_image_path in set(file_paths)
        else file_paths + [query_image_path]
    )
    all_paths, path_to_hash = _hash_paths(all_paths)

    with Session(engine) as session:
        storage = ImageSimilarityEmbeddingStorage(
            session,
            model_name=model_name,
            user_email=user_email,
        )
        paths_for_search, last_reported = _embed_and_store_images(
            session,
            storage,
            all_paths,
            path_to_hash,
            ort_session,
            processor,
            model_name,
            enable_anonymized=enable_anonymized,
        )

        if enable_anonymized:
            _create_private_embeddings(
                session,
                all_paths,
                path_to_hash,
                ort_session,
                processor,
                user_email,
                model_name,
                last_reported=last_reported,
            )

        if enable_anonymized:
            query_row = session.exec(
                select(ImageSimilarityPrivateEmbedding).where(
                    sql_filters.priv_path_in([query_image_path]),
                    sql_filters.priv_model_name_eq(model_name),
                )
            ).first()
        else:
            query_row = session.exec(
                select(ImageSimilarityEmbedding).where(
                    sql_filters.path_eq(query_image_path),
                    sql_filters.model_name_eq(model_name),
                )
            ).first()

        scorer = _build_scorer(
            session,
            scoring_mode,
            query_row,
            query_image_path,
            model_name,
            ort_session,
            processor,
            use_private_table=enable_anonymized,
        )
        search_paths = [p for p in paths_for_search if p != query_image_path]
        raw_results = scorer.score(query_image_path, search_paths, top_k)

        search_results = [
            {**hit, "rank": rank, "is_match": hit["score"] >= min_similarity}
            for rank, hit in enumerate(raw_results, start=1)
        ]

    query_name = os.path.basename(query_image_path)
    file_responses = [
        FileResponse(
            file_type=FileType.IMG,
            path=str(hit["path"]),
            title=f"#{hit['rank']} · similarity {hit['score']}",
            metadata=_build_metadata(hit, scoring_mode, model_name, query_name),
        )
        for rank, hit in enumerate(search_results, start=1)
    ]

    return ResponseBody(root=BatchFileResponse(files=file_responses))


def inputs_cli_parse(value: str) -> Inputs:
    if "|||" not in value:
        raise ValueError(
            "Expected 'input_dir|||query_image_path' (use ||| between folder and query image)."
        )
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
        raise ValueError(
            f"scoring_mode must be one of semantic/pdq/combined, got: {raw_mode!r}"
        )
    scoring_mode = raw_mode
    user_email = parts[4] if len(parts) > 4 and parts[4] else ""
    enable_anonymized = parts[5] if len(parts) > 5 and parts[5] else "no"
    return Parameters(
        model_name=model_name,
        top_k=top_k,
        min_similarity=min_similarity,
        scoring_mode=scoring_mode,
        user_email=user_email,
        enable_anonymized=enable_anonymized,
    )


server.add_ml_service(
    rule="/search_series",
    ml_function=search_series,
    inputs_cli_parser=typer.Argument(
        parser=inputs_cli_parse,
        help="Directory of images and query image as: input_dir|||query_image_path",
    ),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse,
        help="model_name,top_k,min_similarity,scoring_mode  (scoring_mode: combined|semantic|pdq)",
    ),
    short_title="Find series matches (image query)",
    order=0,
    task_schema_func=task_schema,
)


def export_inputs_cli_parse(value: str) -> ExportInputs:
    return ExportInputs(output_dir=DirectoryInput(path=value.strip()))


def export_parameters_cli_parse(value: str) -> ExportParameters:
    return ExportParameters(user_email=value.strip())


server.add_ml_service(
    rule="/export_embeddings",
    ml_function=export_embeddings,
    inputs_cli_parser=typer.Argument(
        parser=export_inputs_cli_parse,
        help="Output directory for the JSONL export file",
    ),
    parameters_cli_parser=typer.Argument(
        parser=export_parameters_cli_parse,
        help="Optional email filter (leave empty for all)",
    ),
    short_title="Export private embeddings",
    order=1,
    task_schema_func=export_task_schema,
)


def import_inputs_cli_parse(value: str) -> ImportInputs:
    return ImportInputs(input_file=FileInput(path=value.strip()))


def import_parameters_cli_parse(value: str) -> ImportParameters:
    return ImportParameters(user_email=value.strip())


server.add_ml_service(
    rule="/import_embeddings",
    ml_function=import_embeddings,
    inputs_cli_parser=typer.Argument(
        parser=import_inputs_cli_parse,
        help="Path to the JSONL file to import",
    ),
    parameters_cli_parser=typer.Argument(
        parser=import_parameters_cli_parse,
        help="Your email (required for audit)",
    ),
    short_title="Import private embeddings",
    order=2,
    task_schema_func=import_task_schema,
)

app = server.app
if __name__ == "__main__":
    app()
