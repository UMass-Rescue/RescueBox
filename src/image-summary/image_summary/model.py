from typing import Final
from pathlib import Path
import logging
import ollama
import torch
import open_clip
import torch.nn.functional as F
from PIL import Image



SUPPORTED_MODELS: Final[dict[str, dict[str, str]]] = {
    "gemma3:4b": {"display_name": "Gemma3 4B: Small, runs on more hardware"},
    "llama3.2-vision:11b": {
        "display_name": "Llama 3.2 11B: More performant, still fits into consumer GPUs",
    },
    "gemma3:27b": {"display_name": "Gemma3 27B: Larger, powerful model"},
    "llama3.2-vision:90b": {
        "display_name": "LLAMA 3.2 90B: Most performant, needs plenty of VRAM",
    },
}

IMAGE_PROMPT: Final[str] = (
    "You are a vision model. Provide a detailed description of the image. "
    "Identify: (1) scene and setting, (2) key objects with attributes (colors, counts, relative positions), "
    "(3) people and actions if present, (4) any visible text (quote verbatim), (5) notable details and context, "
    "(6) lighting, camera angle, and composition if apparent. Be factual and avoid speculation. "
    "Output only the description."
)


def extract_response_after_think(text: str) -> str:
    """
    Extracts and returns the text after the </think> tag.
    """
    tag = "</think>"
    parts = text.split(tag, maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else text.strip()


def ensure_model_exists(model: str) -> None:
    if model not in SUPPORTED_MODELS.keys():
        raise ValueError(
            f"Model '{model}' is not supported. Supported models are: {list(SUPPORTED_MODELS.keys())}"
        )
    try:
        logging.getLogger(__name__).info(
            f"ImageSummary Model: checking availability -> {model}"
        )
        resp = ollama.list()
        models = [m.model for m in resp["models"]]
        if model not in models:
            logging.getLogger(__name__).info(
                f"ImageSummary Model: pulling model -> {model}"
            )
            response = ollama.pull(model)
            if response.status != "success":
                raise ValueError(f"Failed to pull model '{model}': {response}")
    except ValueError as e:
        raise ValueError(e)


def describe_image(model: str, image_path: str) -> str:
    """
    Describe a single image using a vision-capable Ollama model.

    Mirrors the text-summary flow: build a prompt, call ollama.generate,
    and post-process the response (strip any <think> blocks).
    """
    response = ollama.generate(
        model=model,
        prompt=IMAGE_PROMPT,
        images=[image_path],
    )
    if response and response.get("done"):
        return extract_response_after_think(response.get("response", "").strip())
    return str(response)

def rank_images_by_relevance(images: list[Path], target_str: str, clip_model: str="ViT-L-14", pretrained: str="openai") -> list[tuple[str, float]]:
    """
    Rank images by relevance to a target string using CLIP model.

    Returns a list of tuples (image_path, similarity_score) sorted by score descending.
    """
    # Load CLIP model
    clip_model, _, preprocess = open_clip.create_model_and_transforms(clip_model, pretrained=pretrained)
    clip_model.eval()
    
    # device = "cuda" if torch.cuda.is_available() else "cpu"
    # clip_model.to(device)

    # Encode target string
    with torch.no_grad():
        text_tokens = open_clip.tokenize([target_str]) #.to(device)
        text_features = clip_model.encode_text(text_tokens)
        text_features = F.normalize(text_features, p=2, dim=1)

    # Encode images and compute similarity scores
    image_scores = []
    # images = list(iter_image_files(input_path))
    # for image_path in image_paths:
    for image_path in images:
        with torch.no_grad():
            image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0) #.to(device)
            image_features = clip_model.encode_image(image)
            image_features = F.normalize(image_features, p=2, dim=1)

            similarity = (image_features @ text_features.T).item()
            image_scores.append((image_path, similarity))

    # Sort images by similarity score in descending order
    ranked_images = sorted(image_scores, key=lambda x: x[1], reverse=True)
    return ranked_images