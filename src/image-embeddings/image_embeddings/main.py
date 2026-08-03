from __future__ import annotations

import hashlib
import logging
import os
import threading
from functools import cache
from pathlib import Path
from typing import Any, TypedDict, cast

import numpy as np
import onnxruntime as ort
import typer
from pydantic import DirectoryPath
from rb.api.database import ImageEmbedding, engine
from rb.api.embedding_storage import ImageEmbeddingStorage
from rb.api.models import (
    BatchFileResponse,
    EnumParameterDescriptor,
    EnumVal,
    FileFilterDirectory,
    FileResponse,
    FileType,
    FloatRangeDescriptor,
    InputSchema,
    InputType,
    IntRangeDescriptor,
    ParameterSchema,
    RangedFloatParameterDescriptor,
    RangedIntParameterDescriptor,
    ResponseBody,
    TaskSchema,
    TextInput,
)
from rb.lib.job_progress import report_file_progress
from rb.lib.ml_service import MLService
from sqlalchemy import bindparam, text
from sqlmodel import Session, select
from transformers.models.clip.processing_clip import CLIPProcessor

APP_NAME = "image_embeddings"
logger = logging.getLogger(__name__)
# Standard HF CLIP only: ``CLIPModel`` / ``CLIPProcessor`` from the same checkpoint.
# LLM2CLIP and other custom checkpoints are not loadable as ``CLIPModel`` (weight layout differs).
# Must match ``ImageEmbedding.embedding`` in ``rb.api.database`` (pgvector vector(512)).
DEFAULT_CLIP_MODEL = "openai/clip-vit-base-patch32"
_EXPECTED_IMAGE_EMBED_DIM = 512
_CLIP_MODELS_DIR = Path(__file__).resolve().parent / "clip_onnx_models"
# Hugging Face hub uses filelock at DEBUG; keep noise down when root logging is DEBUG.
logging.getLogger("filelock").setLevel(logging.WARNING)

_INSTANCE_LOCK = threading.Lock()

# Raster types accepted for CLIP embedding (top-level files under ``input_dir``).
CLIP_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"}


class ClipImageDirectory(FileFilterDirectory):
    """Directory must exist, be non-empty, and contain at least one allowed image extension."""

    path: DirectoryPath
    file_extensions: list[str] = list(CLIP_IMAGE_EXTENSIONS)


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
    make_threadsafe=True,
)


def _paths_already_embedded(session: Session, paths: list[str]) -> set[str]:
    """Return paths that already have a row in ``image_embeddings`` (reuse for repeat queries)."""
    if not paths:
        return set()
    rows = (
        session.execute(
            select(ImageEmbedding.path).where(
                cast(Any, ImageEmbedding.__table__.c.path).in_(paths)
            )
        )
        .scalars()
        .all()
    )
    return set(rows)


def _sha256_file(path: str) -> str:
    """SHA-256 hex digest of raw file bytes (chunked read for large images)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@cache
def _get_clip_processor() -> Any:
    """Load bundled CLIP tokenizer + image preprocessor (same dir as ONNX exports)."""

    if not (_CLIP_MODELS_DIR / "preprocessor_config.json").is_file():
        raise FileNotFoundError(
            f"Missing CLIP processor files in {_CLIP_MODELS_DIR} "
            f"(preprocessor_config.json alongside text.onnx / vision.onnx)."
        )
    return CLIPProcessor.from_pretrained(
        str(_CLIP_MODELS_DIR),
        local_files_only=True,
        interpolation="bicubic",
    )


@cache
def _get_onnx_sessions() -> tuple[ort.InferenceSession, ort.InferenceSession]:
    """Return (text_session, vision_session) with input validation."""

    text_model = _CLIP_MODELS_DIR / "text.onnx"
    vision_model = _CLIP_MODELS_DIR / "vision.onnx"
    if not text_model.is_file() or not vision_model.is_file():
        raise FileNotFoundError(
            f"Missing CLIP ONNX model files in {_CLIP_MODELS_DIR}: text.onnx/vision.onnx"
        )
    available_providers = ort.get_available_providers()
    providers = []
    if "CUDAExecutionProvider" in available_providers:
        providers = [
            (
                "CUDAExecutionProvider",
                {"device_id": 0, "cudnn_conv_algo_search": "DEFAULT"},
            ),
        ]
    if "CoreMLExecutionProvider" in available_providers:
        providers.append("CoreMLExecutionProvider")

    providers.append("CPUExecutionProvider")
    text_candidate = ort.InferenceSession(str(text_model), providers=providers)
    vision_candidate = ort.InferenceSession(str(vision_model), providers=providers)

    return text_candidate, vision_candidate


def _pick_session_for_inputs(
    sessions: tuple[ort.InferenceSession, ort.InferenceSession],
    inputs: dict,
    label: str,
) -> tuple[ort.InferenceSession, set[str]]:
    input_keys = set(inputs.keys())
    candidates = [
        (session, {inp.name for inp in session.get_inputs()}) for session in sessions
    ]

    if label == "vision":
        # Prefer a pure-vision encoder (pixel_values only).
        for session, names in candidates:
            if "pixel_values" in names and "input_ids" not in names:
                return session, names
        for session, names in candidates:
            if "pixel_values" in names:
                return session, names
        raise ValueError(
            f"Unable to match ONNX vision inputs. Provided={sorted(input_keys)}"
        )

    if label == "text":
        # Prefer a pure-text encoder (input_ids/attention_mask only).
        for session, names in candidates:
            if "input_ids" in names and "pixel_values" not in names:
                return session, names
        for session, names in candidates:
            if "input_ids" in names:
                return session, names
        raise ValueError(
            f"Unable to match ONNX text inputs. Provided={sorted(input_keys)}"
        )

    for session, names in candidates:
        if names.issubset(input_keys):
            return session, names
    raise ValueError(
        f"Unable to match ONNX {label} inputs. Provided={sorted(input_keys)}"
    )


def _clip_image_processor(processor: Any) -> Any:
    """Return the vision preprocessor (``CLIPProcessor`` exposes it at runtime)."""
    return getattr(processor, "image_processor", None)


def _dummy_text_inputs(processor) -> dict:
    inputs = dict(processor(text=[""], return_tensors="np", padding=True))
    return {
        "input_ids": inputs.get("input_ids"),
        "attention_mask": inputs.get("attention_mask"),
    }


def _dummy_pixel_values(processor) -> np.ndarray:
    from PIL import Image

    size = getattr(_clip_image_processor(processor), "size", 224)
    if isinstance(size, dict):
        size = max(size.values() or [224])
    dummy = Image.new("RGB", (int(size), int(size)), color=(0, 0, 0))
    inputs = dict(processor(images=dummy, return_tensors="np", do_rescale=True))
    return inputs["pixel_values"]


def search_images(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    """
    Embed images under ``input_dir`` that are not already stored, then rank
    those images (including reused embeddings) by CLIP text–image similarity to ``query``.
    """
    from PIL import Image

    with _INSTANCE_LOCK:
        input_dir = str(inputs["input_dir"].path)
        query_text = inputs["query"].text

        model_name = parameters.get("model_name", DEFAULT_CLIP_MODEL)
        top_k = int(parameters.get("top_k", 15))
        min_similarity = float(parameters.get("min_similarity", 0.13))
        expected_dim = _EXPECTED_IMAGE_EMBED_DIM

        processor = _get_clip_processor()
        text_session, vision_session = _get_onnx_sessions()
        _img_proc = _clip_image_processor(processor)
        logger.info(
            "CLIP ONNX sessions loaded model_name=%s do_normalize=%s resample=%s",
            model_name,
            getattr(_img_proc, "do_normalize", None),
            getattr(_img_proc, "resample", None),
        )
        dummy_text = _dummy_text_inputs(processor)
        dummy_pixels = _dummy_pixel_values(processor)

        file_paths: list[str] = []
        for name in sorted(os.listdir(input_dir)):
            path = os.path.join(input_dir, name)
            if (
                os.path.isfile(path)
                and os.path.splitext(path)[1].lower() in CLIP_IMAGE_EXTENSIONS
            ):
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
            total_paths = len(file_paths)
            processed_paths = 0
            last_reported = 0

            for path in file_paths:
                try:
                    if path in already:
                        paths_for_search.append(path)
                        reused_count += 1
                        continue
                    h = path_to_hash[path]
                    row = (
                        session.execute(
                            select(ImageEmbedding).where(
                                ImageEmbedding.content_sha256 == h
                            )
                        )
                        .scalars()
                        .first()
                    )
                    if row is None:
                        try:
                            image = Image.open(path).convert("RGB")
                            inputs_processed = dict(
                                processor(
                                    images=image, return_tensors="np", do_rescale=True
                                )
                            )
                            vision_inputs = {**inputs_processed, **dummy_text}
                            onnx_session, required = _pick_session_for_inputs(
                                (text_session, vision_session),
                                vision_inputs,
                                "vision",
                            )
                            if "pixel_values" not in required:
                                raise ValueError(
                                    f"Vision ONNX session missing pixel_values input: {sorted(required)}"
                                )
                            outputs = onnx_session.run(
                                ["image_embeds"],
                                {
                                    k: v
                                    for k, v in vision_inputs.items()
                                    if k in required
                                },
                            )
                            image_features = outputs[0]
                            if image_features.shape[-1] != expected_dim:
                                raise ValueError(
                                    f"CLIP ONNX vision output dim={image_features.shape[-1]}; "
                                    f"image_embeddings.embedding is vector({expected_dim})."
                                )
                            image_features = image_features / np.linalg.norm(
                                image_features, axis=-1, keepdims=True
                            )
                            embedding = image_features.squeeze()
                            embedding_list = embedding.tolist()
                            storage.save_embedding(
                                path, embedding_list, content_sha256=h
                            )
                            paths_for_search.append(path)
                            newly_embedded_count += 1
                            already.add(path)
                            session.flush()
                        except Exception as e:
                            logger.warning("Could not process %s: %s", path, e)
                            continue
                    if row is not None:
                        row_path_str = str(row.path)
                        if row_path_str == path or os.path.normpath(
                            row_path_str
                        ) == os.path.normpath(path):
                            paths_for_search.append(path)
                            reused_count += 1
                            already.add(path)
                            session.flush()
                            continue
                        if row_path_str not in file_paths_set:
                            row.path = path
                            session.add(row)
                            relocated_count += 1
                            logger.info(
                                "Reused image embedding by content hash (path updated): %s -> %s",
                                row.path,
                                path,
                            )
                        else:
                            emb = (
                                list(row.embedding) if row.embedding is not None else []
                            )
                            session.add(
                                ImageEmbedding(
                                    path=path, embedding=emb, content_sha256=h
                                )
                            )
                            cloned_count += 1
                        paths_for_search.append(path)
                        reused_count += 1
                        already.add(path)
                        session.flush()
                        continue
                finally:
                    processed_paths += 1
                    last_reported = report_file_progress(
                        None, processed_paths, total_paths, last_reported
                    )

            if total_paths > 0:
                report_file_progress(None, total_paths, total_paths, last_reported)

            if newly_embedded_count or relocated_count or cloned_count:
                storage.commit()

            text_inputs = dict(
                processor(text=[query_text], return_tensors="np", padding=True)
            )
            text_inputs["pixel_values"] = dummy_pixels
            onnx_session, required = _pick_session_for_inputs(
                (text_session, vision_session),
                text_inputs,
                "text",
            )
            if "input_ids" not in required:
                raise ValueError(
                    f"Text ONNX session missing input_ids input: {sorted(required)}"
                )
            text_outputs = onnx_session.run(
                ["text_embeds"],
                {k: v for k, v in text_inputs.items() if k in required},
            )
            text_features = text_outputs[0]
            text_features = text_features / np.linalg.norm(
                text_features, axis=-1, keepdims=True
            )
            query_vec = text_features.squeeze()

            embedded_paths = paths_for_search
            if embedded_paths:
                # pgvector: rank only rows whose path was embedded in this run (uses index on embedding).
                qvec_literal = "[" + ",".join(str(x) for x in query_vec.tolist()) + "]"
                stmt = text(
                    """
                        SELECT id, path, 1 - (embedding <=> CAST(:qvec AS vector)) AS similarity
                        FROM image_embeddings
                        WHERE path IN :paths
                        ORDER BY embedding <=> CAST(:qvec AS vector)
                        LIMIT :top_k
                        """
                ).bindparams(bindparam("paths", expanding=True))
                rows = session.execute(
                    stmt,
                    {"qvec": qvec_literal, "paths": embedded_paths, "top_k": top_k},
                ).fetchall()
                search_results = []
                for row in rows:
                    sim = float(row.similarity)
                    search_results.append(
                        {
                            # "id": row.id,
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
                    subtitle=query_text,
                    metadata={
                        "Query": query_text,
                        "Similarity": str(sim),
                        "Match": "Yes" if is_match else "No",
                        # "Model": model_name,
                        # "id": str(row.get("id", "")),
                    },
                )
            )

        batch = BatchFileResponse(files=file_responses)
        return ResponseBody(root=batch)


def inputs_cli_parse(value: str) -> Inputs:
    """CLI: ``input_dir|||query`` (triple pipe separates directory from query text)."""
    if "|||" not in value:
        raise ValueError(
            "Expected 'input_dir|||query' (use ||| between folder path and search text)."
        )
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
