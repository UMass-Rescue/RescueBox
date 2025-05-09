import os
import subprocess
import shutil
from typing import TypedDict
from rb.lib.ml_service import MLService
from rb.api.models import (
    ParameterSchema,
    TaskSchema,
    ResponseBody,
    TextResponse,
    BatchTextResponse,
    FileInput,
    InputSchema,
    InputType,
    DirectoryInput,
    FileResponse,
    EnumParameterDescriptor,
    EnumVal,
    IntParameterDescriptor
)
from datetime import datetime
from pathlib import Path
import typer
import ollama
import logging
import whisper
import csv
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

APP_NAME="video_summarizer"

VIDEO_PATH = "video.mp4"
FRAME_FOLDER = "video_frames/"
MODEL_NAME = "gemma3:4b"
AUDIO_PATH = "extracted_audio.wav"

class Inputs(TypedDict):
    input_file: FileInput
    output_directory: DirectoryInput

class Parameters(TypedDict):
    fps: int  
    audio_tran: str

def create_video_summary_schema() -> TaskSchema:
    input_schema = InputSchema(
        key="input_file",
        label="Video file to summarize",
        input_type=InputType.FILE,
    )
    output_schema = InputSchema(
        key="output_directory",
        label="Path to save results",
        input_type=InputType.DIRECTORY,
    )
    fps_param_schema = ParameterSchema(
        key="fps",
        label="Frame Rate (fps)",
        subtitle="Set how many frames per second to extract from the video",
        value={
        "parameterType": "int",
        "default": 1
        },
    )
    audio_tran_schema = ParameterSchema(
        key="audio_tran",
        label="Do you want to transcribe audio?",
        value=EnumParameterDescriptor(
        enumVals=[
            EnumVal(key="yes", label="Yes"),
            EnumVal(key="no", label="No")
        ],
        default="yes"
        )
    )

    return TaskSchema(inputs=[input_schema, output_schema], parameters=[fps_param_schema, audio_tran_schema])

def clean_caption_formatting(caption):
    if not isinstance(caption, str):
        caption = str(caption)

    # Replace newlines and carriage returns with a space
    caption = caption.replace('\n', ' ').replace('\r', ' ')

    # Replace multiple spaces with a single space
    caption = re.sub(r'\s+', ' ', caption)

    # Trim leading/trailing spaces
    return caption.strip()

def extract_frames_ffmpeg(video_path, output_folder, fps=1):
    os.makedirs(output_folder, exist_ok=True)
    output_pattern = os.path.join(output_folder, "frame_%04d.jpg")
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps={fps}",
        output_pattern
    ]
    subprocess.run(command, check=True)

def extract_audio_ffmpeg(video_path, audio_path=AUDIO_PATH):
    command = [
        "ffmpeg",
        "-i", video_path,
        "-q:a", "0",
        "-map", "a",
        audio_path,
        "-y"
    ]
    subprocess.run(command, check=True)

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result['text']

def summarize_video(inputs: Inputs, parameters: Parameters):  

    fps = parameters.get("fps", 1)

    # Step 1: Extract frames from the video
    Path(FRAME_FOLDER).mkdir(parents=True, exist_ok=True)
    extract_frames_ffmpeg(inputs["input_file"].path, FRAME_FOLDER, fps=fps)
    
    images = sorted([
        os.path.join(FRAME_FOLDER, f)
        for f in os.listdir(FRAME_FOLDER)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])

    # Step 2: Extract audio and transcribe it if needed
    audio_transcribe = parameters.get("audio_tran", "yes") == "yes"
    if audio_transcribe:
        extract_audio_ffmpeg(inputs["input_file"].path, AUDIO_PATH)
        transcribed_text = transcribe_audio(AUDIO_PATH)
    else:
        transcribed_text = "No audio transcription was requested."

    # Step 3: Prepare output paths
    out_path = Path(inputs["output_directory"].path)
    out_path_captions = str(out_path / f"captions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    out_path_transcription = str(out_path / f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    out_path_summary = str(out_path / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")


    # Step 4: Describe each frame
    ollama.generate(MODEL_NAME, "You will receive frames from a video in sequence, one at a time. For each frame, generate a concise one-sentence description.")

    summaries = {}
    for idx, image in enumerate(images, start=1):
        prompt = f"This is frame {idx} of the video. Summarize it in one sentence."
        try:
            response = ollama.generate(MODEL_NAME, prompt, images=[image])
            formatted_response = clean_caption_formatting(response['response'])
            summaries[idx] = formatted_response
        except Exception as e:
            summaries[idx] = f"Error - {e}"

    # Step 5: Summarize the whole video using both visual + audio data
    if audio_transcribe:
        summary_prompt = (
            "Here are one-sentence descriptions of each frame of a video:\n" +
            "\n".join(f"Frame {frame_id}: {caption}" for frame_id, caption in summaries.items()) + 
            "\nHere is the transcribed audio from the video:\n" +
            transcribed_text +
            "\nSummarize the overall video in a few sentences using both visual and audio context."
        )
    else:
        summary_prompt = (
        "Here are one-sentence descriptions of each frame of a video:\n" +
        "\n".join(f"Frame {frame_id}: {caption}" for frame_id, caption in summaries.items()) +
        "\nSummarize the overall video in a few sentences. Keep in mind that certain frames occuring one after the other could be describing the same incident that has just occured."
        )

    final_response = ollama.generate(MODEL_NAME, summary_prompt)
    final_summary = final_response['response']

    # Step 6: Write results to files
    with open(out_path_captions, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Frame", "Caption"])  # Header

        for frame_id, caption in summaries.items():
            writer.writerow([f"Frame {frame_id}", caption])
    
    if audio_transcribe:
        with open(out_path_transcription, 'w', encoding='utf-8') as f:
            f.write(transcribed_text.strip())

    with open(out_path_summary, 'w', encoding='utf-8') as f:
        f.write(final_summary.strip())

    shutil.rmtree(FRAME_FOLDER, ignore_errors=True)
    if os.path.exists(AUDIO_PATH):
        os.remove(AUDIO_PATH)

    return ResponseBody(FileResponse(path=out_path_summary, file_type="text"))

def inputs_cli_parse(input: str) -> Inputs:
    input_file, output_directory = input.split(",")
    input_file = Path(input_file)
    output_directory = Path(output_directory)
    if not input_file.exists():
        raise ValueError("Input file does not exist.")
    if not output_directory.exists():
        output_directory.mkdir(parents=True, exist_ok=True)
    return Inputs(
        input_file=FileInput(path=input_file),
        output_directory=DirectoryInput(path=output_directory),
    )

def parameters_cli_parse(params: str) -> Parameters:
    fps_str, audio_tran = params.split(",")
    return Parameters(fps=int(fps_str), audio_tran=audio_tran.strip())

server=MLService(APP_NAME)
server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Video Summarization",
    author="Sachin Thomas & Priyanka Bengaluru Anil",
    version="1.0.0",
    info="Video Summarization with audio transcription."
)

server.add_ml_service(
    rule="/summarize-video",
    ml_function=summarize_video,
    inputs_cli_parser=typer.Argument(
        parser=inputs_cli_parse, help="Input file and output directory paths"
    ),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse, help="Set how many frames per second to extract from the video"
    ),
    short_title="Video Summarization",
    order=0,
    task_schema_func=create_video_summary_schema,
)

app = server.app
if __name__ == "__main__":
    app()

