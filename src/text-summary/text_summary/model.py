import ollama
from text_summary.summary_prompt import PROMPT

SUPPORTED_MODELS = [
    "gemma3:1b",
    "gemma3:4b",
    "deepseek-r1:1.5b",
    "deepseek-r1:7b",
    "llama3.2:3b",
]


def extract_response_after_think(text: str) -> str:
    """
    Extracts and returns the text after the </think> tag.
    """
    tag = "</think>"
    parts = text.split(tag, maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else text.strip()


def ensure_model_exists(model: str) -> None:
    if model not in SUPPORTED_MODELS:
        raise ValueError(
            f"Model '{model}' is not supported. Supported models are: {SUPPORTED_MODELS}"
        )
    try:
        response = ollama.pull(model)
    except ollama.ResponseError as e:
        raise ValueError(e.error)
    if response.status != "success":
        raise ValueError(f"Failed to pull model '{model}': {response}")


def summarize(model: str, text: str) -> str:
    prompt = PROMPT.format(text=text)
    response = ollama.generate(model, prompt)
    if response and response["done"]:
        response = extract_response_after_think(response["response"])
    return response
