from typing import TypedDict
import hashlib
import logging
import os
import threading

import numpy as np
import typer
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


def task_schema() -> TaskSchema:
    model_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(key="apple/DFN5B-CLIP-ViT-H-14-378", label="CLIP-ViT-H-14-378-Apple"),
        ],
        default="apple/DFN5B-CLIP-ViT-H-14-378",
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


def _embed_and_store_images(session, storage, file_paths, path_to_hash, model, processor, device, _inputs_to_device):
    """Ensure every path has an embedding row in ``image_embeddings``. Returns paths ready for search."""
    import torch
    from PIL import Image

    already = _paths_already_embedded(session, file_paths)
    file_paths_set = set(file_paths)
    paths_for_search: list[str] = []
    newly_embedded = relocated = cloned = 0

    for path in file_paths:
        if path in already:
            paths_for_search.append(path)
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
                            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                            storage.save_embedding(
                                path, image_features.squeeze().cpu().numpy().tolist(), content_sha256=h,
                            )
                        paths_for_search.append(path)
                        newly_embedded += 1
                        already.add(path)
                        session.flush()
                    except Exception as e:
                        logger.warning("Could not process %s: %s", path, e)
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


def search_similar_images(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    """Find images visually similar to a query image inside ``input_dir``."""
    apply_torch_cpu_preference()
    import torch
    from PIL import Image
    from transformers import CLIPProcessor, CLIPModel  # type: ignore

    input_dir = str(inputs["input_dir"].path)
    query_image_path = str(inputs["query_image"].path)
    model_name = parameters.get("model_name", "apple/DFN5B-CLIP-ViT-H-14-378")
    top_k = int(parameters.get("top_k", 5))
    min_similarity = float(parameters.get("min_similarity", 0.5))

    cuda_ok = torch.cuda.is_available()
    mps_ok = bool(getattr(torch.backends, "mps", None)) and torch.backends.mps.is_available()
    if cuda_ok:
        device = torch.device("cuda")
    elif mps_ok:
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    logger.info("CLIP runtime: cuda_available=%s mps_available=%s -> selected device=%s", cuda_ok, mps_ok, device)
    if cuda_ok and device.type == "cuda":
        try:
            idx = torch.cuda.current_device()
            logger.info("CUDA GPU in use: name=%s index=%s", torch.cuda.get_device_name(idx), idx)
        except Exception as e:
            logger.debug("Could not read CUDA device name: %s", e)
    elif device.type == "mps":
        logger.info("Apple Metal (MPS) GPU in use for CLIP")

    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    model = model.to(device)
    model.eval()
    logger.info("CLIP model loaded on device=%s model_name=%s", device, model_name)

    def _inputs_to_device(batch):
        return {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}

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
            session, storage, all_paths, path_to_hash, model, processor, device, _inputs_to_device,
        )

        # Reuse query embedding from DB when available.
        query_row = session.exec(
            select(ImageEmbedding).where(ImageEmbedding.path == query_image_path)
        ).first()

        if query_row is not None and query_row.embedding is not None:
            query_vec = np.array(list(query_row.embedding), dtype=np.float32)
        else:
            image = Image.open(query_image_path).convert("RGB")
            with torch.no_grad():
                inputs_processed = _inputs_to_device(
                    processor(images=image, return_tensors="pt", do_rescale=True)
                )
                image_features = model.get_image_features(**inputs_processed)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                query_vec = image_features.squeeze().cpu().numpy()

        search_paths = [p for p in paths_for_search if p != query_image_path]
        search_results: list[dict] = []
        if search_paths:
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
            for row in rows:
                sim = float(row.similarity)
                search_results.append({
                    "id": row.id, "path": row.path,
                    "similarity": round(sim, 4), "is_match": sim >= min_similarity,
                })

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
    model_name = parts[0] if len(parts) > 0 and parts[0] else "apple/DFN5B-CLIP-ViT-H-14-378"
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
