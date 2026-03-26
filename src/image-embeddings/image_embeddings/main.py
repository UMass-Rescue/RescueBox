from typing import TypedDict
import json

import typer
from rb.lib.ml_service import MLService
from rb.api.models import (
    InputSchema,
    InputType,
    ParameterSchema,
    EnumParameterDescriptor,
    EnumVal,
    RangedIntParameterDescriptor,
    IntRangeDescriptor,
    ResponseBody,
    TaskSchema,
    DirectoryInput,
    TextInput,
    TextResponse,
)
from rb.api.database import engine, ImageEmbedding
from rb.api.embedding_storage import ImageEmbeddingStorage
from sqlmodel import Session


APP_NAME = "image_embeddings"


class Inputs(TypedDict):
    input_dir: DirectoryInput


class Parameters(TypedDict):
    model_name: str


def task_schema() -> TaskSchema:
    image_schema = InputSchema(
        key="input_dir",
        label="Provide directory of image files",
        input_type=InputType.DIRECTORY,
    )

    model_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(key="openai/clip-vit-base-patch32", label="CLIP ViT-B/32 (Base)"),
            EnumVal(key="openai/clip-vit-large-patch14", label="CLIP ViT-L/14 (Large)"),
        ],
        default="openai/clip-vit-base-patch32",
    )

    return TaskSchema(
        inputs=[image_schema],
        parameters=[
            ParameterSchema(
                key="model_name",
                label="CLIP model",
                subtitle="Hugging Face CLIP model to compute embeddings",
                value=model_enum,
            ),
        ],
    )


server = MLService(APP_NAME)
server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Image Embeddings",
    author="UMass Rescue",
    version="3.0.0",
    info="Create embeddings for images using CLIP models.",
)


def embed_images(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    import os
    import numpy as np
    from PIL import Image
    from transformers import CLIPProcessor, CLIPModel  # type: ignore
    import torch

    input_dir = str(inputs["input_dir"].path)
    model_name = parameters.get("model_name", "openai/clip-vit-base-patch32")

    # Load CLIP model and processor
    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    
    # Set model to evaluation mode
    model.eval()

    # Supported image extensions
    allowed_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    file_paths: list[str] = []
    
    for name in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, name)
        if os.path.isfile(path) and os.path.splitext(path)[1].lower() in allowed_exts:
            file_paths.append(path)

    results: dict[str, list[float]] = {}
    
    with Session(engine) as session:
        storage = ImageEmbeddingStorage(session)
        
        for path in file_paths:
            try:
                # Load and process image
                image = Image.open(path).convert("RGB")
                
                # Process image and get embeddings
                with torch.no_grad():
                    inputs_processed = processor(images=image, return_tensors="pt")
                    image_features = model.get_image_features(**inputs_processed)
                    
                    # Normalize embeddings
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    
                    # Convert to numpy and then to list
                    embedding = image_features.squeeze().cpu().numpy()
                    embedding_list = embedding.tolist()
                    results[path] = embedding_list
                    
                    # Save to database using storage interface
                    storage.save_embedding(path, embedding_list)
                    
            except Exception as e:
                # Skip files that can't be processed
                print(f"Warning: Could not process {path}: {e}")
                continue
        
        # Commit all embeddings at once
        storage.commit()

    response = TextResponse(
        value=json.dumps(results),
        title="Image Embeddings",
        subtitle=f"files={len(results)}, model={model_name}",
    )
    return ResponseBody(root=response)


def inputs_cli_parse(value: str) -> Inputs:
    return Inputs(input_dir=DirectoryInput(path=value))


def parameters_cli_parse(value: str) -> Parameters:
    # Accept model name as parameter
    model_name = value.strip() if value.strip() else "openai/clip-vit-base-patch32"
    return Parameters(model_name=model_name)


server.add_ml_service(
    rule="/embed_images",
    ml_function=embed_images,
    inputs_cli_parser=typer.Argument(parser=inputs_cli_parse, help="Directory of image files"),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse,
        help="model_name (default: openai/clip-vit-base-patch32)",
    ),
    short_title="Image Embeddings",
    order=0,
    task_schema_func=task_schema,
)


# ============================================================================
# Search Endpoint - Text-to-Image Search
# ============================================================================

class SearchInputs(TypedDict):
    query: TextInput


class SearchParameters(TypedDict):
    model_name: str
    top_k: int


def search_task_schema() -> TaskSchema:
    query_schema = InputSchema(
        key="query",
        label="Search query (text)",
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

    return TaskSchema(
        inputs=[query_schema],
        parameters=[
            ParameterSchema(
                key="model_name",
                label="CLIP model",
                subtitle="Must match the model used for embedding",
                value=model_enum,
            ),
            ParameterSchema(
                key="top_k",
                label="Top K results",
                subtitle="Number of most similar images to return",
                value=top_k_desc,
            ),
        ],
    )


def search_images(inputs: SearchInputs, parameters: SearchParameters) -> ResponseBody:
    """
    Search for similar image embeddings using text query via CLIP.
    
    Uses CLIP's text encoder to embed the query, then searches for similar
    image embeddings using pgvector's optimized cosine distance operator.
    This enables cross-modal text-to-image search.
    """
    from transformers import CLIPProcessor, CLIPModel  # type: ignore
    import torch

    query_text = inputs["query"].text
    model_name = parameters.get("model_name", "openai/clip-vit-base-patch32")
    top_k = int(parameters.get("top_k", 5))

    # Load CLIP model and processor
    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    model.eval()

    # Generate text embedding using CLIP's text encoder
    with torch.no_grad():
        text_inputs = processor(text=[query_text], return_tensors="pt", padding=True)
        text_features = model.get_text_features(**text_inputs)
        
        # Normalize embeddings (same as image embeddings)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        # Convert to numpy
        query_embedding = text_features.squeeze().cpu().numpy()

    # Search using pgvector's optimized cosine distance operator
    with Session(engine) as session:
        from sqlalchemy import text as sql_text
        
        # Convert embedding to proper format for pgvector
        embedding_str = "[" + ",".join(str(x) for x in query_embedding.tolist()) + "]"
        
        query = sql_text(f"""
            SELECT 
                id,
                path,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM image_embeddings
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT :top_k
        """)
        
        results = session.execute(
            query,
            {
                "top_k": top_k
            }
        ).fetchall()

    # Format results
    search_results = []
    for row in results:
        search_results.append({
            "id": row.id,
            "path": row.path,
            "similarity": float(row.similarity),
        })

    response_data = {
        "query": query_text,
        "model": model_name,
        "top_k": top_k,
        "results": search_results,
    }

    response = TextResponse(
        value=json.dumps(response_data, indent=2),
        title="Image Search Results (Text Query)",
        subtitle=f"Found {len(search_results)} similar images using {model_name}",
    )
    return ResponseBody(root=response)


def search_inputs_cli_parse(value: str) -> SearchInputs:
    return SearchInputs(query=TextInput(text=value))


def search_parameters_cli_parse(value: str) -> SearchParameters:
    # Accept comma-separated values: model_name,top_k
    parts = [p.strip() for p in value.split(",")]
    model_name = parts[0] if len(parts) > 0 and parts[0] else "openai/clip-vit-base-patch32"
    top_k = int(parts[1]) if len(parts) > 1 and parts[1] else 5
    return SearchParameters(
        model_name=model_name,
        top_k=top_k,
    )


server.add_ml_service(
    rule="/search_images",
    ml_function=search_images,
    inputs_cli_parser=typer.Argument(parser=search_inputs_cli_parse, help="Search query text"),
    parameters_cli_parser=typer.Argument(
        parser=search_parameters_cli_parse,
        help="model_name,top_k",
    ),
    short_title="Search Images (Text Query)",
    order=1,
    task_schema_func=search_task_schema,
)


app = server.app
if __name__ == "__main__":
    app()
