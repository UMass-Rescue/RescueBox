"""audio transcribe plugin"""

import logging
from typing import List, TypedDict

from pydantic import DirectoryPath
import typer

# 1. Import the shared_task decorator from the central Celery setup
from celery import shared_task

from rb.api.models import (
    BatchTextResponse,
    DirectoryInput,
    FileFilterDirectory,
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
    version="2.1.0", # Version bump for new feature
    info="A parser for transcribing audio files (now with async support).",
)

model = AudioTranscriptionModel()

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac"}


class AudioDirectory(FileFilterDirectory):
    path: DirectoryPath
    file_extensions: List[str] = AUDIO_EXTENSIONS


class AudioInput(TypedDict):
    input_dir: AudioDirectory


def _transcribe_logic(inputs: AudioInput) -> ResponseBody:
    """
    Core transcription logic, separated from the Celery task wrapper.
    This function can be called directly by a synchronous endpoint.
    """
    # The 'inputs' argument is a TypedDict, so we use dictionary key access.
    dirpath = DirectoryPath(inputs["input_dir"].path)
    results = model.transcribe_files_in_directory(dirpath)

    result_texts = [
        TextResponse(value=r["result"], title=str(r["file_path"])) for r in results
    ]
    response = BatchTextResponse(texts=result_texts)
    return ResponseBody(root=response)


def task_schema() -> TaskSchema:
    input_schema = InputSchema(
        key="input_dir",
        label="Provide audio files directory",
        input_type=InputType.DIRECTORY,
    )
    return TaskSchema(inputs=[input_schema], parameters=[])


# 2. The core logic is wrapped in a `@shared_task` decorator, turning it into a Celery task.
#    This allows it to be executed asynchronously by a Celery worker.
@shared_task(bind=True)
def transcribe_task(self, inputs: AudioInput) -> ResponseBody:
    """
    This is the Celery task that performs the long-running transcription.
    It runs in the background, allowing the API to remain responsive.
    The `bind=True` argument gives access to the task instance (`self`)
    which contains metadata like the unique task ID (`self.request.id`).
    """
    logger.info(f"Task {self.request.id}: Starting async transcription.")
    # This Celery task now simply calls the core logic function.
    response = _transcribe_logic(inputs)
    logger.info(f"Task {self.request.id}: Async transcription finished.")
    return response


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


# 3. Register the Celery task as an asynchronous service with the MLService helper.
ml_service.add_ml_service(
    rule="/transcribe",
    # For a synchronous endpoint (is_async=False), we pass the core logic function.
    # If is_async were True, we would pass the Celery task `transcribe_task`.
    ml_function=transcribe_task,
    inputs_cli_parser=typer.Argument(parser=cli_parser, help="Input directory path"),
    task_schema_func=task_schema,
    short_title="Transcribe audio files",
    order=0,
    help="Transcribe audio files (starts an async job).",
    # Setting `is_async=True` is the key that tells MLService to set up the
    # two-step async workflow (task creation and result polling endpoints).
    is_async=False
)

app = ml_service.app
if __name__ == "__main__":
    app()
