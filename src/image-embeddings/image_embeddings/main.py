from typing import TypedDict
import os

import typer
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
    TextInput,
    BatchFileResponse,
    FileResponse,
    FileType,
)
from rb.api.database import ImageEmbedding, engine
from rb.api.embedding_storage import ImageEmbeddingStorage
from sqlmodel import Session, select
from sqlalchemy import bindparam, text


APP_NAME = "image_embeddings"


class Inputs(TypedDict):
    input_dir: DirectoryInput
    query: TextInput


class Parameters(TypedDict):
    model_name: str
    top_k: int
    min_similarity: float


def task_schema() -> TaskSchema:
    input_dir_schema = InputSchema(
        key="input_dir",
        label="Directory of image files to embed and search",
        input_type=InputType.DIRECTORY,
    )
    query_schema = InputSchema(
        key="query",
        label="Text query to find the most similar images",
        input_type=InputType.TEXT,
    )

    model_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(key="openai/clip-vit-base-patch32", label="CLIP ViT-B/32 (Base)"),
            EnumVal(key="openai/clip-vit-large-patch14", label="CLIP ViT-L/14 (Large)"),
        ],
        default="openai/clip-vit-base-patch32",
    )

    top_k_desc = RangedIntParameterDescriptor(
        range=IntRangeDescriptor(min=1, max=20),
        default=5,
    )
    min_similarity_desc = RangedFloatParameterDescriptor(
        range=FloatRangeDescriptor(min=0.0, max=1.0),
        default=0.21,
    )

    return TaskSchema(
        inputs=[input_dir_schema, query_schema],
        parameters=[
            ParameterSchema(
                key="model_name",
                label="CLIP model",
                subtitle="CLIP stays fuzzy on queries like 'boy' use a caption 'a young boy' for better results",
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
                subtitle="Similarity >= this counts as a match (CLIP text–image scores are often ~0.2–0.35)",
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
    name="Image Embeddings",
    author="UMass Rescue",
    version="3.0.0",
    info=info,
    gpu=False,
)


def _paths_already_embedded(session: Session, paths: list[str]) -> set[str]:
    """Return paths that already have a row in ``image_embeddings`` (reuse for repeat queries)."""
    if not paths:
        return set()
    rows = session.exec(select(ImageEmbedding.path).where(ImageEmbedding.path.in_(paths))).all()
    return set(rows)


def search_images(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    """
    Embed images under ``input_dir`` that are not already stored, then rank
    those images (including reused embeddings) by CLIP text–image similarity to ``query``.
    """
    import torch
    from PIL import Image
    from transformers import CLIPProcessor, CLIPModel  # type: ignore

    input_dir = str(inputs["input_dir"].path)
    query_text = inputs["query"].text
    model_name = parameters.get("model_name", "openai/clip-vit-base-patch32")
    top_k = int(parameters.get("top_k", 5))
    min_similarity = float(parameters.get("min_similarity", 0.21))

    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    model.eval()

    allowed_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    file_paths: list[str] = []
    for name in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, name)
        if os.path.isfile(path) and os.path.splitext(path)[1].lower() in allowed_exts:
            file_paths.append(path)

    paths_for_search: list[str] = []
    newly_embedded_count = 0
    reused_count = 0
    search_results: list[dict] = []

    with Session(engine) as session:
        storage = ImageEmbeddingStorage(session)
        already = _paths_already_embedded(session, file_paths)

        for path in file_paths:
            if path in already:
                paths_for_search.append(path)
                reused_count += 1
                continue
            try:
                image = Image.open(path).convert("RGB")
                with torch.no_grad():
                    inputs_processed = processor(images=image, return_tensors="pt")
                    image_features = model.get_image_features(**inputs_processed)
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    embedding = image_features.squeeze().cpu().numpy()
                    embedding_list = embedding.tolist()
                    storage.save_embedding(path, embedding_list)
                paths_for_search.append(path)
                newly_embedded_count += 1
            except Exception as e:
                print(f"Warning: Could not process {path}: {e}")
                continue

        if newly_embedded_count:
            storage.commit()

        with torch.no_grad():
            text_inputs = processor(text=[query_text], return_tensors="pt", padding=True)
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
                        "id": row.id,
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
                    "Model": model_name,
                    "id": str(row.get("id", "")),
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
    return Inputs(
        input_dir=DirectoryInput(path=dir_part.strip()),
        query=TextInput(text=query_part.strip()),
    )


def parameters_cli_parse(value: str) -> Parameters:
    parts = [p.strip() for p in value.split(",")]
    model_name = parts[0] if len(parts) > 0 and parts[0] else "openai/clip-vit-base-patch32"
    top_k = int(parts[1]) if len(parts) > 1 and parts[1] else 5
    min_similarity = float(parts[2]) if len(parts) > 2 and parts[2] else 0.21
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
