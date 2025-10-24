from typing import TypedDict
from pathlib import Path
from PIL import Image
import typer
import onnxruntime as ort
from transformers import BlipProcessor
from huggingface_hub import hf_hub_download
from typing import Dict
import numpy as np
# import tensorflow as tf
# from keras.preprocessing.image import load_img, img_to_array

from rb.lib.ml_service import MLService
from rb.api.models import (
    TaskSchema,
    InputSchema,
    InputType,
    TextResponse,
    FileInput
)

# --- Instructions for the User ---
# See the README for instructions on how to generate the required ONNX model files.
# ----------------------------------

APP_NAME = "caption_blip"

# --- Model Configuration ---
MODEL_DIR = Path(__file__).parent.parent / "models"
VISION_MODEL_PATH = MODEL_DIR / "vision_model.onnx"
TEXT_MODEL_PATH = MODEL_DIR / "text_decoder_model.onnx"
HUGGINGFACE_MODEL = "Salesforce/blip-image-captioning-large"

# --- Global variables ---
vision_session = None
text_session = None
processor = None
service = MLService(APP_NAME)
app = service.app

def download_blip_processor_files(repo_id: str, local_dir: Path):
    """Downloads necessary BlipProcessor files to a local directory."""
    local_dir.mkdir(parents=True, exist_ok=True)

    files_to_download = [
        "preprocessor_config.json",
        "tokenizer_config.json",
        "vocab.txt",
        "special_tokens_map.json",
        "tokenizer.json", # For fast tokenizer
        "added_tokens.json" # If any
    ]

    for filename in files_to_download:
        try:
            hf_hub_download(repo_id=repo_id, filename=filename, local_dir=local_dir)
        except Exception as e:
            print(f"Warning: Could not download {filename}. It might not exist for this model. Error: {e}")

def load_models():
    """Loads the ONNX models and the processor."""
    global vision_session, text_session, processor
    if vision_session is not None: # Models already loaded
        return

    if not VISION_MODEL_PATH.exists() or not TEXT_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"ONNX model files not found. Searched in '{MODEL_DIR}'. "
            f"Please refer to the plugin's README to generate the models."
        )
    
    vision_session = ort.InferenceSession(str(VISION_MODEL_PATH))
    text_session = ort.InferenceSession(str(TEXT_MODEL_PATH))

    # Define a local directory for processor files
    local_processor_dir = MODEL_DIR / "blip_processor_files"
    download_blip_processor_files(HUGGINGFACE_MODEL, local_processor_dir)
    
    processor = BlipProcessor.from_pretrained(str(local_processor_dir))

def captioning_task_schema() -> TaskSchema:
    """Defines the schema for the captioning task."""
    return TaskSchema(
        inputs=[
            InputSchema(
                key="input_file",
                label="Image File",
                subtitle="Select an image to generate a caption for.",
                input_type=InputType.FILE,
            )
        ],
        parameters=[]
    )

class Inputs(TypedDict):
    input_file: FileInput

def generate_caption(inputs: Inputs) -> TextResponse:
    """Generates a caption for a single image file."""
    load_models()

    image_path = inputs["input_file"].path
    image = Image.open(image_path).convert("RGB")

    # Preprocess image
    text = "a photography of"
    pixel_values = processor(images=image, text=text, return_tensors="np").pixel_values

    # Get image embeddings from the vision model
    vision_outputs = vision_session.run(None, {'pixel_values': pixel_values})
    image_embeds = vision_outputs[0]

    # Autoregressive generation
    decoder_input_ids = np.array([[processor.tokenizer.pad_token_id]], dtype=np.int64)
    encoder_attention_mask = np.ones(image_embeds.shape[:-1], dtype=np.int64)

    generated_ids_list = []

    for _ in range(32):  # Max length of caption
        attention_mask = np.ones(decoder_input_ids.shape, dtype=np.int64)

        text_outputs = text_session.run(None, {
            'input_ids': decoder_input_ids,
            'attention_mask': attention_mask,
            'encoder_hidden_states': image_embeds,
            'encoder_attention_mask': encoder_attention_mask
        })

        next_token_logits = text_outputs[0][:, -1, :]
        next_token_id = np.argmax(next_token_logits, axis=-1)

        # Stop if EOS token is generated
        if next_token_id[0] == processor.tokenizer.eos_token_id:
            break
        
        generated_ids_list.append(next_token_id[0])

        # Prepare input for the next iteration
        decoder_input_ids = np.concatenate([decoder_input_ids, next_token_id[:, np.newaxis]], axis=1)

    # Decode the caption
    caption = processor.decode(generated_ids_list, skip_special_tokens=True)

    return TextResponse(value=caption.strip(), title="Generated Caption")



service.add_app_metadata(
    plugin_name=APP_NAME,
    name="Caption Image BLIP",
    author="UMass Rescue",
    version="1.0.0",
    info=(
        "This plugin lets you  get a caption descriptions for an image . "
        "For each image, it desscribes key objects and their attributes , "
        "baby/boy/girl/man/woman for person and visible text. "
        "Input: a file image. Output: a text containing the description."
    ),
)

# Add the ML service to the application
service.add_ml_service(
    rule="/caption",
    ml_function=generate_caption,
    task_schema_func=captioning_task_schema,
    inputs_cli_parser=typer.Argument(
        ..., help="Path to the image file."
    ),
    short_title="Generate Image Caption",
    order=0,
)