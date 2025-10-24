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
    ResponseBody,
    TaskSchema,
    DirectoryInput,
    TextResponse,
)


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
    version="1.0.0",
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
                results[path] = embedding.tolist()
                
        except Exception as e:
            # Skip files that can't be processed
            print(f"Warning: Could not process {path}: {e}")
            continue

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


app = server.app
if __name__ == "__main__":
    app()
