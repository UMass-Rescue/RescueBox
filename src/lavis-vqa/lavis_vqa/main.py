from typing import TypedDict
from pathlib import Path
from PIL import Image
import typer
import torch
from typing import Dict, List

from lavis.models import load_model_and_preprocess

from rb.lib.ml_service import MLService
from rb.api.models import (
    TaskSchema,
    InputSchema,
    InputType,
    TextResponse,
    FileInput
)

APP_NAME = "lavis_vqa"

# --- Model Configuration ---
LAVIS_MODEL_NAME = "blip_vqa"
LAVIS_MODEL_TYPE = "vqav2"
# name="blip_vqa", model_type="vqav2"
# https://github.com/salesforce/LAVIS/issues/724
# vqav2, okvqa, aokvqa

# --- Global variables ---
model = None
processor = None
device = "cuda" if torch.cuda.is_available() else "cpu"
service = MLService(APP_NAME)
app = service.app

def load_lavis_model():
    """Loads the LAVIS BLIP-VQA model and processor."""
    global model, processor, txt_processor
    if model is not None: # Models already loaded
        return

    model, processor, txt_processor = load_model_and_preprocess(
        name=LAVIS_MODEL_NAME,
        model_type=LAVIS_MODEL_TYPE,
        is_eval=True,
        device=device
    )

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

def ask_image_details_lavis(inputs: Inputs) -> TextResponse:
    """Asks generic questions about an image to extract details using LAVIS."""
    load_lavis_model()

    image_path = inputs['input_file'].path
    raw_image = Image.open(image_path).convert("RGB")

    generic_questions = [
        "What is in the image?",
        "What are the tools in this image?",
        "What are the items in this image?",
        "What is the furniture in this image?",
        "What does any sign say?",
        "Describe the main objects.",
        "What colors are prominent?",
        "how many people?",
        "what action is each person doing?",
        "What is the setting or environment?",
        "Describe the overall scene."
    ]

    # Preprocess image
    image = processor["eval"](raw_image).unsqueeze(0).to(device)
    
    all_answers = []

    for question_text in generic_questions:
        # Preprocess question
        # LAVIS processor handles question preprocessing internally when passed to model.generate
        
        # Generate answer
        # BLIP-VQA in LAVIS expects image and question as separate inputs to generate
        answer = model.predict_answers(samples={"image": image, "text_input": question_text},
                                        inference_method="generate",max_len=40)
        all_answers.append(f"Q: {question_text}\nA: {answer[0]}") # answer is a list

    return TextResponse(value="\n\n".join(all_answers), title="Image Details (LAVIS)")

service.add_app_metadata(
    plugin_name=APP_NAME,
    name="Image Details VQA (LAVIS)",
    author="UMass Rescue",
    version="1.0.0",
    info=(
        "This plugin uses Visual Question Answering (VQA) via LAVIS to extract detailed information from images. "
        "It asks a set of generic questions about the image and provides the answers."
    ),
)

# Add the ML service to the application
service.add_ml_service(
    rule="/ask_details_lavis",
    ml_function=ask_image_details_lavis,
    task_schema_func=ask_details_task_schema,
    inputs_cli_parser=typer.Argument(
        ..., help="Path to the image file."
    ),
    short_title="Ask Image Details (LAVIS)",
    order=0,
)
