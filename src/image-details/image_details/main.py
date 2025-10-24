from typing import TypedDict
from pathlib import Path
from PIL import Image
import typer
import torch
from transformers import BlipForQuestionAnswering, AutoProcessor
from huggingface_hub import hf_hub_download

from rb.lib.ml_service import MLService
from rb.api.models import (
    TaskSchema,
    InputSchema,
    InputType,
    TextResponse,
    FileInput
)

APP_NAME = "image_details"

# --- Model Configuration ---
HUGGINGFACE_VQA_MODEL = "Salesforce/blip-vqa-base"
MODEL_DIR = Path(__file__).parent.parent / "models"

# --- Global variables ---
model = None
processor = None
device = "cuda" if torch.cuda.is_available() else "cpu"
service = MLService(APP_NAME)
app = service.app

def download_vqa_model_files(repo_id: str, local_dir: Path):
    """Downloads necessary BlipForQuestionAnswering model and processor files to a local directory."""
    local_dir.mkdir(parents=True, exist_ok=True)

    # Files for AutoProcessor (tokenizer and preprocessor)
    files_to_download = [
        "preprocessor_config.json",
        "tokenizer_config.json",
        "vocab.txt",
        "special_tokens_map.json",
        "tokenizer.json", # For fast tokenizer
        "added_tokens.json", # If any
        "config.json" # Model config
    ]

    for filename in files_to_download:
        try:
            hf_hub_download(repo_id=repo_id, filename=filename, local_dir=local_dir)
        except Exception as e:
            print(f"Warning: Could not download {filename}. It might not exist for this model. Error: {e}")

    # Model weights (PyTorch)
    try:
        hf_hub_download(repo_id=repo_id, filename="pytorch_model.bin", local_dir=local_dir)
    except Exception as e:
        print(f"Error: Could not download pytorch_model.bin. Error: {e}")
        raise

def load_vqa_model():
    """Loads the BlipForQuestionAnswering model and processor."""
    global model, processor
    if model is not None: # Models already loaded
        return

    local_model_dir = MODEL_DIR / "blip_vqa_model_files"
    download_vqa_model_files(HUGGINGFACE_VQA_MODEL, local_model_dir)
    
    model = BlipForQuestionAnswering.from_pretrained(str(local_model_dir)).to(device)
    processor = AutoProcessor.from_pretrained(str(local_model_dir))

def ask_details_task_schema() -> TaskSchema:
    """Defines the schema for the ask_details task."""
    return TaskSchema(
        inputs=[
            InputSchema(
                key="input_file",
                label="Image File",
                subtitle="Select an image to ask questions about.",
                input_type=InputType.FILE,
            )
        ],
        parameters=[]
    )

class Inputs(TypedDict):
    input_file: FileInput

def ask_image_details(inputs: Inputs) -> TextResponse:
    """Asks generic questions about an image to extract details."""
    load_vqa_model()
    print("debug input_file path:",  inputs["input_file"].path)
    
    image_path = inputs["input_file"].path
    image = Image.open(image_path).convert("RGB")

    generic_questions = [
        "what are the tools in this image?",
        "what are the items in this image?",
        "what is the furniture in this image?",
        "what does any sign say?",
        "What colors are prominent?",
        "how many people?",
        "what action is each person doing?",
    ]

    # Preprocess image
    pixel_values = processor.image_processor(image, return_tensors="pt").to(device)
    
    all_answers = []

    with torch.no_grad():
        # Compute image embedding
        vision_outputs = model.vision_model(pixel_values=pixel_values["pixel_values"])
        image_embeds = vision_outputs[0]
        image_attention_mask = torch.ones(image_embeds.size()[:-1], dtype=torch.long).to(image_embeds.device)
        
        for question_text in generic_questions:
            # Preprocess question
            question = processor.tokenizer(text=question_text, return_tensors="pt").to(device)
            
            # Compute text encodings
            question_outputs = model.text_encoder(
                input_ids=question["input_ids"],
                attention_mask=None, # Attention mask for text encoder is not always needed for VQA
                encoder_hidden_states=image_embeds,
                encoder_attention_mask=image_attention_mask,
                return_dict=False,
            )
            question_embeds = question_outputs[0]
            question_attention_mask = torch.ones(question_embeds.size()[:-1], dtype=torch.long).to(question_embeds.device)
            
            bos_ids = torch.full(
                (question_embeds.size(0), 1), fill_value=model.decoder_start_token_id, device=question_embeds.device
            )

            outputs = model.text_decoder.generate(
                input_ids=bos_ids,
                eos_token_id=model.config.text_config.sep_token_id,
                pad_token_id=model.config.text_config.pad_token_id,
                encoder_hidden_states=question_embeds,
                encoder_attention_mask=question_attention_mask,
            )
            for i in range(len(outputs)):
                answer = processor.decode(outputs[i], skip_special_tokens=False)
                all_answers.append(f"Q: {question_text}\nA: {answer}")
        
    return TextResponse(value="\n\n".join(all_answers), title="Image Details")

service.add_app_metadata(
    plugin_name=APP_NAME,
    name="Image Details VQA",
    author="UMass Rescue",
    version="1.0.0",
    info=(
        "This plugin uses Visual Question Answering (VQA) to extract detailed information from images. "
        "It asks a set of generic questions about the image and provides the answers."
    ),
)

# Add the ML service to the application
service.add_ml_service(
    rule="/ask_details",
    ml_function=ask_image_details,
    task_schema_func=ask_details_task_schema,
    inputs_cli_parser=typer.Argument(
        ..., help="Path to the image file."
    ),
    short_title="Ask Image Details",
    order=0,
)
