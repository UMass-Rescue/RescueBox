# transcription_only.py
from typing import TypedDict
from pathlib import Path
from rb.lib.ml_service import MLService
from rb.api.models import (
    DirectoryInput,
    FileResponse,
    InputSchema,
    InputType,
    ResponseBody,
    TaskSchema,
)

import whisper
import json

# Load ASR model
asr_model = whisper.load_model("medium.en")

class TranscriptionInputs(TypedDict):
    input_dir: DirectoryInput
    output_dir: DirectoryInput

class TranscriptionParameters(TypedDict):
    pass

def create_task_schema() -> TaskSchema:
    input_schema = InputSchema(
        key="input_dir",
        label="Path to the directory containing audio files",
        input_type=InputType.DIRECTORY
    )
    output_schema = InputSchema(
        key="output_dir",
        label="Path to the output directory",
        input_type=InputType.DIRECTORY
    )
    return TaskSchema(inputs=[input_schema, output_schema], parameters=[])

def is_audio_file(file_path: Path) -> bool:
    audio_extensions = {".wav", ".mp3", ".flac", ".ogg"}
    return file_path.suffix.lower() in audio_extensions

server = MLService(__name__)
server.add_app_metadata(
    name="Audio Transcription",
    author="Christina, Swetha, Nikita",
    version="1.0",
    info="app-info.md"
)

@server.route("/transcribe", task_schema_func=create_task_schema, short_title="Audio Transcription")
def transcribe(inputs: TranscriptionInputs, parameters: TranscriptionParameters) -> ResponseBody:
    input_path = Path(inputs["input_dir"].path)
    output_path = Path(inputs["output_dir"].path)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}

    audio_files = [input_path] if input_path.is_file() else list(input_path.glob("*"))

    for audio_file in audio_files:
        if is_audio_file(audio_file):
            try:
                print(f"Transcribing {audio_file.name}...")
                asr_result = asr_model.transcribe(str(audio_file))
                results[audio_file.name] = asr_result["text"]
            except Exception as e:
                results[audio_file.name] = f"Error: {str(e)}"
        else:
            results[audio_file.name] = "Error: Not a valid audio file"

    output_file = output_path / "transcription_output.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    return ResponseBody(FileResponse(path=str(output_file), file_type="json"))

if __name__ == "__main__":
    server.run()