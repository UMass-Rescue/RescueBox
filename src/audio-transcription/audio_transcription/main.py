"""audio transcribe plugin"""

import logging
from typing import TypedDict

from pathlib import Path
from pydantic import DirectoryPath, field_validator
import typer
from rb.api.models import (
    BatchTextResponse,
    DirectoryInput,
    InputSchema,
    InputType,
    ResponseBody,
    TextResponse,
    TaskSchema,
)
from audio_transcription.model import AudioTranscriptionModel
from rb.lib.ml_service import MLService

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

APP_NAME = "audio"
ml_service = MLService(APP_NAME)
ml_service.add_app_metadata(
    plugin_name=APP_NAME,
    name="Audio Transcription",
    author="RescueBox Team",
    version="2.0.0",
    info="A parser for transcribing audio files.",
)

model = AudioTranscriptionModel()

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac"}


class AudioDirectory(DirectoryInput):
    path: DirectoryPath

    @field_validator("path")
    @classmethod
    def validate_directory(cls, v):
        path = Path(v)

        if not path.exists():
            raise ValueError(f"validate Directory: '{v}' does not exist.")
        if not path.is_dir():
            raise ValueError(f"validate Directory: Path '{v}' is not a directory.")

        audio_files = list(path.glob("*"))
        if not audio_files:
            raise ValueError("validate Directory: Directory is empty.")

        no_audio = [f.name for f in audio_files if f.suffix.lower() in AUDIO_EXTENSIONS]

        if len(no_audio) < 1:
            raise ValueError(
                f"validate Directory: No-audio files found in directory: {no_audio}"
            )

        return v


class AudioInput(TypedDict):
    input_dir: AudioDirectory


def task_schema() -> TaskSchema:
    input_schema = InputSchema(
        key="input_dir",
        label="Provide audio files directory",
        input_type=InputType.DIRECTORY,
    )
    return TaskSchema(inputs=[input_schema], parameters=[])


def transcribe(inputs: AudioInput) -> ResponseBody:
    """Transcribe audio files"""

    print("Processing transcription...")
    dirpath = inputs["input_dir"].path

    results = model.transcribe_files_in_directory(dirpath)
    result_texts = [
        TextResponse(value=r["result"], title=r["file_path"]) for r in results
    ]

    print(f"Transcription Results: {results}")
    response = BatchTextResponse(texts=result_texts)
    return ResponseBody(root=response)


def cli_parser(path: str):
    """
    Parses CLI input path into a Pydantic object.
    """
    try:
        logger.debug(f"Parsing CLI input path: {path}")
        return AudioInput(input_dir=DirectoryInput(path=path))
    except Exception as e:
        logger.error(f"Error parsing CLI input: {e}")
        raise typer.Abort()


ml_service.add_ml_service(
    rule="/transcribe",
    ml_function=transcribe,
    inputs_cli_parser=typer.Argument(parser=cli_parser, help="Input directory path"),
    task_schema_func=task_schema,
    short_title="Transcribe audio files",
    order=0,
)

app = ml_service.app
if __name__ == "__main__":
    app()
