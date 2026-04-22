from __future__ import annotations

from typing import Any, List, TypedDict
import hashlib
import logging
import os
import threading

import typer
from pydantic import DirectoryPath
from rb.lib.ml_service import MLService
from rb.lib.utils import apply_torch_cpu_preference
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
    FileFilterDirectory,
    TextInput,
    BatchFileResponse,
    FileResponse,
    FileType,
)
from rb.api.database import ImageEmbedding, engine
from rb.api.embedding_storage import ImageEmbeddingStorage
from sqlmodel import Session, select
from sqlalchemy import bindparam, text, update


APP_NAME = "image_embeddings"
logger = logging.getLogger(__name__)
# Standard HF CLIP only: ``CLIPModel`` / ``CLIPProcessor`` from the same checkpoint.
# LLM2CLIP and other custom checkpoints are not loadable as ``CLIPModel`` (weight layout differs).
# Must match ``ImageEmbedding.embedding`` in ``rb.api.database`` (pgvector vector(768)).
DEFAULT_CLIP_MODEL = "openai/clip-vit-large-patch14-336"
_EXPECTED_IMAGE_EMBED_DIM = 768
# Hugging Face hub uses filelock at DEBUG; keep noise down when root logging is DEBUG.
logging.getLogger("filelock").setLevel(logging.WARNING)

# Serialize embed + insert per content hash within this OS process only (multi-worker / multi-host
# deployments still need DB or distributed locks).
_EMBED_LOCKS_GUARD = threading.Lock()
_EMBED_LOCKS: dict[str, threading.Lock] = {}

# Concurrent HTTP workers may call ``search_images`` at once; Hugging Face ``transformers`` lazy
# exports can race on first import ("cannot import name 'CLIPProcessor'"). Serialize CLIP class
# resolution and prefer submodule imports (avoid ``transformers`` package __init__ entirely).
_CLIP_IMPORT_LOCK = threading.Lock()
_CLIP_MODEL_CLS: type | None = None
_CLIP_PROCESSOR_CLS: type | None = None

# Serialize CLIP weight load + ``.to(device)``. Prefer eager Hub ``load_state_dict`` (CPU tensors) —
# HF ``from_pretrained`` builds with ``meta`` placeholders on some transformers/CUDA stacks and
# ``model.to(cuda)`` fails. Fallback to ``from_pretrained`` only if Hub has no single-file checkpoint.
_CLIP_INSTANCE_LOCK = threading.Lock()
_CLIP_INSTANCE_CACHE: dict[tuple[str, str], tuple[Any, Any]] = {}

# Raster types accepted for CLIP embedding (top-level files under ``input_dir``).
CLIP_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"}


class ClipImageDirectory(FileFilterDirectory):
    """Directory must exist, be non-empty, and contain at least one allowed image extension."""

    path: DirectoryPath
    file_extensions: List[str] = list(CLIP_IMAGE_EXTENSIONS)


def _lock_for_content_hash(content_sha256_hex: str) -> threading.Lock:
    with _EMBED_LOCKS_GUARD:
        lock = _EMBED_LOCKS.get(content_sha256_hex)
        if lock is None:
            lock = threading.Lock()
            _EMBED_LOCKS[content_sha256_hex] = lock
        return lock


class Inputs(TypedDict):
    input_dir: ClipImageDirectory
    query: TextInput


class Parameters(TypedDict):
    model_name: str
    top_k: int
    min_similarity: float

def task_schema() -> TaskSchema:
    input_dir_schema = InputSchema(
        key="input_dir",
        label="Directory of image files to search",
        input_type=InputType.DIRECTORY,
    )
    query_schema = InputSchema(
        key="query",
        label="Enter Text query to find the most similar images",
        input_type=InputType.TEXT,
    )

  
    model_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(
                key=DEFAULT_CLIP_MODEL,
                label=DEFAULT_CLIP_MODEL,
            ),
        ],
        default=DEFAULT_CLIP_MODEL,
    )

    top_k_desc = RangedIntParameterDescriptor(
        range=IntRangeDescriptor(min=1, max=20),
        default=10,
    )
    min_similarity_desc = RangedFloatParameterDescriptor(
        range=FloatRangeDescriptor(min=0.0, max=1.0),
        default=0.13,
    )

    return TaskSchema(
        inputs=[input_dir_schema, query_schema],
        parameters=[
            ParameterSchema(
                key="model_name",
                label="CLIP model",
                subtitle="search for images with a ML model",
                value=model_enum,
            ),
            ParameterSchema(
                key="top_k",
                label="Top K results",
                subtitle="Number of highest-similarity images to return",
                value=top_k_desc,
            ),
            ParameterSchema(
                key="min_similarity",
                label="Match threshold",
                subtitle="Similarity >= this counts as a match ( often > 0.13)",
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
    name="Search Images",
    author="UMass RescueLab",
    version="3.0.0",
    info=info,
    gpu=True,
)


def _paths_already_embedded(session: Session, paths: list[str]) -> set[str]:
    """Return paths that already have a row in ``image_embeddings`` (reuse for repeat queries)."""
    if not paths:
        return set()
    rows = session.exec(select(ImageEmbedding.path).where(ImageEmbedding.path.in_(paths))).all()
    return set(rows)


def _sha256_file(path: str) -> str:
    """SHA-256 hex digest of raw file bytes (chunked read for large images)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_clip_classes() -> tuple[type, type]:
    """Return ``(CLIPModel, CLIPProcessor)`` (cached, thread-safe)."""
    global _CLIP_MODEL_CLS, _CLIP_PROCESSOR_CLS
    if _CLIP_MODEL_CLS is not None and _CLIP_PROCESSOR_CLS is not None:
        return _CLIP_MODEL_CLS, _CLIP_PROCESSOR_CLS
    with _CLIP_IMPORT_LOCK:
        if _CLIP_MODEL_CLS is not None and _CLIP_PROCESSOR_CLS is not None:
            return _CLIP_MODEL_CLS, _CLIP_PROCESSOR_CLS
        try:
            from transformers.models.clip.modeling_clip import CLIPModel
            from transformers.models.clip.processing_clip import CLIPProcessor
        except ImportError:
            from transformers import CLIPModel, CLIPProcessor  # type: ignore

        _CLIP_MODEL_CLS = CLIPModel
        _CLIP_PROCESSOR_CLS = CLIPProcessor
        logger.debug("CLIP classes bound (thread-safe lazy init)")
        return _CLIP_MODEL_CLS, _CLIP_PROCESSOR_CLS


def _clip_model_load_pretrained_cpu(model_cls: type, model_name: str) -> Any:
    """
    Instantiate CLIP from config and ``load_state_dict`` from Hub files — real CPU tensors only.

    Avoids HF ``from_pretrained``'s meta-device construction path so ``model.to(cuda)`` cannot hit
    "Cannot copy out of meta tensor".
    """
    import torch
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import EntryNotFoundError

    cfg = model_cls.config_class.from_pretrained(model_name)
    model = model_cls(cfg)

    weight_path: str | None = None
    last_err: BaseException | None = None
    for fn in ("model.safetensors", "pytorch_model.bin"):
        try:
            weight_path = hf_hub_download(repo_id=model_name, filename=fn)
            break
        except EntryNotFoundError as exc:
            last_err = exc


    if weight_path.endswith(".safetensors"):
        from safetensors.torch import load_file

        sd = load_file(weight_path, device="cpu")
    else:
        sd = torch.load(weight_path, map_location=torch.device("cpu"), weights_only=True)

    incomp = model.load_state_dict(sd, strict=False)
    if incomp.missing_keys:
        logger.warning(
            "CLIP load_state_dict missing %d keys (showing first 5): %s",
            len(incomp.missing_keys),
            incomp.missing_keys[:5],
        )

    return model


def _get_clip_model_and_processor(model_name: str, device: Any) -> tuple[Any, Any]:
    """
    Return a loaded CLIP model and processor, reusing a process-wide cache per (model, device).

    Serializes the full load + ``.to(device)`` under a lock so parallel requests do not call
    ``from_pretrained`` / ``.to(cuda)`` concurrently (avoids meta-tensor errors on some stacks).
    """
    import torch

    if device.type == "cuda":
        try:
            dev_key = f"cuda:{torch.cuda.current_device()}"
        except Exception:
            dev_key = "cuda:0"
    elif device.type == "mps":
        dev_key = "mps"
    else:
        dev_key = "cpu"

    key = (model_name, dev_key)
    with _CLIP_INSTANCE_LOCK:
        hit = _CLIP_INSTANCE_CACHE.get(key)
        if hit is not None:
            logger.debug("CLIP instance cache hit: %s @ %s", model_name, dev_key)
            return hit

        CLIPModel, CLIPProcessor = _get_clip_classes()
        logger.info(
            "Loading CLIP weights (cache key %s, %s) for shared use across requests",
            model_name,
            dev_key,
        )
        model = _clip_model_load_pretrained_cpu(CLIPModel, model_name)
        processor = CLIPProcessor.from_pretrained(
            model_name, interpolation="bicubic"
        )
        for tensor in list(model.parameters()) + list(model.buffers()):
            if getattr(tensor, "is_meta", False):
                raise RuntimeError(
                    f"CLIP {model_name!r} still has meta tensors after eager CPU weight load."
                )
        model = model.to(device)
        model.eval()
        _CLIP_INSTANCE_CACHE[key] = (model, processor)
        return model, processor


def search_images(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    """
    Embed images under ``input_dir`` that are not already stored, then rank
    those images (including reused embeddings) by CLIP text–image similarity to ``query``.
    """
    apply_torch_cpu_preference()
    import torch
    from PIL import Image

    input_dir = str(inputs["input_dir"].path)
    query_text = inputs["query"].text

    model_name = parameters.get("model_name", DEFAULT_CLIP_MODEL)
    top_k = int(parameters.get("top_k", 15))
    min_similarity = float(parameters.get("min_similarity", 0.13))

    cuda_ok = torch.cuda.is_available()
    mps_ok = bool(getattr(torch.backends, "mps", None)) and torch.backends.mps.is_available()
    if cuda_ok:
        device = torch.device("cuda")
    elif mps_ok:
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    logger.info(
        "CLIP runtime: cuda_available=%s mps_available=%s -> selected device=%s",
        cuda_ok,
        mps_ok,
        device,
    )
    if cuda_ok and device.type == "cuda":
        try:
            idx = torch.cuda.current_device()
            logger.info(
                "CUDA GPU in use: name=%s index=%s",
                torch.cuda.get_device_name(idx),
                idx,
            )
        except Exception as e:
            logger.debug("Could not read CUDA device name: %s", e)
    elif device.type == "mps":
        logger.info("Apple Metal (MPS) GPU in use for CLIP")

    model, processor = _get_clip_model_and_processor(model_name, device)
    param_dev = next(model.parameters()).device
    _pdim = getattr(model.config, "projection_dim", None)
    if _pdim != _EXPECTED_IMAGE_EMBED_DIM:
        raise ValueError(
            f"CLIP model {model_name!r} has projection_dim={_pdim}; PostgreSQL "
            f"image_embeddings.embedding is vector({_EXPECTED_IMAGE_EMBED_DIM}). "
            f"Use {DEFAULT_CLIP_MODEL!r}, or change the DB column and this check together."
        )
    logger.info(
        "CLIP model loaded on device=%s (parameter device=%s) model_name=%s projection_dim=%s "
        "do_normalize=%s resample=%s",
        device,
        param_dev,
        model_name,
        _pdim,
        getattr(processor.image_processor, "do_normalize", None),
        getattr(processor.image_processor, "resample", None),
    )

    def _inputs_to_device(batch):
        """Move HuggingFace processor tensors to ``device`` for CLIP forward passes."""
        return {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}

    file_paths: list[str] = []
    for name in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, name)
        if os.path.isfile(path) and os.path.splitext(path)[1].lower() in CLIP_IMAGE_EXTENSIONS:
            file_paths.append(path)

    path_to_hash: dict[str, str] = {}
    hashed_paths: list[str] = []
    for path in file_paths:
        try:
            path_to_hash[path] = _sha256_file(path)
            hashed_paths.append(path)
        except OSError as exc:
            logger.warning("Skip hashing %s: %s", path, exc)
    file_paths = hashed_paths

    paths_for_search: list[str] = []
    newly_embedded_count = 0
    relocated_count = 0
    cloned_count = 0
    reused_count = 0
    search_results: list[dict] = []

    with Session(engine) as session:
        storage = ImageEmbeddingStorage(session)
        already = _paths_already_embedded(session, file_paths)
        file_paths_set = set(file_paths)

        for path in file_paths:
            if path in already:
                paths_for_search.append(path)
                reused_count += 1
                continue
            h = path_to_hash[path]
            row = session.exec(
                select(ImageEmbedding).where(ImageEmbedding.content_sha256 == h)
            ).first()
            if row is None:
                with _lock_for_content_hash(h):
                    row = session.exec(
                        select(ImageEmbedding).where(ImageEmbedding.content_sha256 == h)
                    ).first()
                    if row is None:
                        try:
                            image = Image.open(path).convert("RGB")
                            with torch.no_grad():
                                inputs_processed = _inputs_to_device(
                                    processor(images=image, return_tensors="pt", do_rescale=True)
                                )
                                image_features = model.get_image_features(**inputs_processed)
                                image_features = image_features / image_features.norm(
                                    dim=-1, keepdim=True
                                )
                                embedding = image_features.squeeze().cpu().numpy()
                                embedding_list = embedding.tolist()
                                storage.save_embedding(path, embedding_list, content_sha256=h)
                            paths_for_search.append(path)
                            newly_embedded_count += 1
                            already.add(path)
                            session.flush()
                        except Exception as e:
                            logger.warning("Could not process %s: %s", path, e)
                        continue
            if row is not None:
                if row.path == path:
                    paths_for_search.append(path)
                    reused_count += 1
                    already.add(path)
                    session.flush()
                    continue
                if row.path not in file_paths_set:
                    session.execute(
                        update(ImageEmbedding)
                        .where(ImageEmbedding.id == row.id)
                        .values(path=path)
                    )
                    relocated_count += 1
                    logger.info(
                        "Reused image embedding by content hash (path updated): %s -> %s",
                        row.path,
                        path,
                    )
                else:
                    emb = list(row.embedding) if row.embedding is not None else []
                    session.add(
                        ImageEmbedding(path=path, embedding=emb, content_sha256=h)
                    )
                    cloned_count += 1
                paths_for_search.append(path)
                reused_count += 1
                already.add(path)
                session.flush()
                continue

        if newly_embedded_count or relocated_count or cloned_count:
            storage.commit()

        with torch.no_grad():
            text_inputs = _inputs_to_device(
                processor(text=[query_text], return_tensors="pt", padding=True, do_rescale=True)
            )
            text_features = model.get_text_features(**text_inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            query_vec = text_features.squeeze().cpu().numpy()

        embedded_paths = paths_for_search
        if embedded_paths:
            # pgvector: rank only rows whose path was embedded in this run (uses index on embedding).
            qvec_literal = "[" + ",".join(str(x) for x in query_vec.tolist()) + "]"
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
                stmt,
                {"qvec": qvec_literal, "paths": embedded_paths, "top_k": top_k},
            ).fetchall()
            search_results = []
            for row in rows:
                sim = float(row.similarity)
                search_results.append(
                    {
                        #"id": row.id,
                        "path": row.path,
                        "similarity": round(sim, 4),
                        "is_match": sim >= min_similarity,
                    }
                )

    # One FileResponse per ranked hit so job UI uses the same batch table as age-gender (click row → open image).
    file_responses: list[FileResponse] = []
    for rank, row in enumerate(search_results, start=1):
        sim = row["similarity"]
        is_match = row["is_match"]
        path = str(row["path"])
        file_responses.append(
            FileResponse(
                file_type=FileType.IMG,
                path=path,
                title=f"#{rank} · similarity {sim}",
                subtitle=query_text[:120] + ("…" if len(query_text) > 120 else ""),
                metadata={
                    "Query": query_text,
                    "Similarity": str(sim),
                    "Match": "Yes" if is_match else "No",
                    #"Model": model_name,
                    #"id": str(row.get("id", "")),
                },
            )
        )

    batch = BatchFileResponse(files=file_responses)
    return ResponseBody(root=batch)


def inputs_cli_parse(value: str) -> Inputs:
    """CLI: ``input_dir|||query`` (triple pipe separates directory from query text)."""
    if "|||" not in value:
        raise ValueError("Expected 'input_dir|||query' (use ||| between folder path and search text).")
    dir_part, query_part = value.split("|||", 1)
    try:
        return Inputs(
            input_dir=ClipImageDirectory(path=dir_part.strip()),
            query=TextInput(text=query_part.strip()),
        )
    except Exception as e:
        logger.error("Error parsing CLI inputs: %s", e)
        raise typer.Abort() from e


def parameters_cli_parse(value: str) -> Parameters:
    parts = [p.strip() for p in value.split(",")]
    model_name = parts[0] if len(parts) > 0 and parts[0] else DEFAULT_CLIP_MODEL
    top_k = int(parts[1]) if len(parts) > 1 and parts[1] else 5
    min_similarity = float(parts[2]) if len(parts) > 2 and parts[2] else 0.113
    return Parameters(
        model_name=model_name,
        top_k=top_k,
        min_similarity=min_similarity,
    )


server.add_ml_service(
    rule="/search_images",
    ml_function=search_images,
    inputs_cli_parser=typer.Argument(
        parser=inputs_cli_parse,
        help="Directory of images and search query as: input_dir|||query",
    ),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse,
        help="model_name,top_k,min_similarity",
    ),
    short_title="Embed images and search (text query)",
    order=0,
    task_schema_func=task_schema,
)


app = server.app
if __name__ == "__main__":
    app()
