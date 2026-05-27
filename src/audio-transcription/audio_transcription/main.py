"""audio transcribe plugin"""

import errno
import hashlib
import os
import logging
from pathlib import Path
from typing import List, TypedDict

from pydantic import DirectoryPath
import typer
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

script_dir = os.path.dirname(os.path.abspath(__file__))
info_file_path = os.path.join(script_dir, "app-info.md")
with open(info_file_path, "r") as f:
    info = f.read()

ml_service.add_app_metadata(
    plugin_name=APP_NAME,
    name="Transcribe Audio",
    author="UMass RescueLab",
    version="3.0.0",
    info=info,
    make_threadsafe=False,
)

model = AudioTranscriptionModel()

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}


class AudioDirectory(FileFilterDirectory):

    path: DirectoryPath
    file_extensions: List[str] = AUDIO_EXTENSIONS


class AudioInput(TypedDict):
    input_dir: AudioDirectory


def _resolve_transcripts_dir(dirpath: Path) -> Path:
    """
    Prefer ``<input_dir>/transcripts``. If the input lives on a read-only mount (e.g. UFDR
    FUSE), use a writable folder under the system temp instead.
    """
    preferred = dirpath / "transcripts"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred.resolve()
    except OSError as e:
        if e.errno not in (errno.EROFS, errno.EACCES, errno.EPERM):
            raise
        key = hashlib.sha256(str(dirpath.resolve()).encode("utf-8")).hexdigest()[:16]
        base = Path(os.environ.get("TMPDIR", "/tmp")) / "rescuebox-audio-transcripts"
        fallback = (base / key).resolve()
        fallback.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Input dir not writable for transcripts (%s); writing .txt files under %s",
            e,
            fallback,
        )
        return fallback


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
    dirpath = Path(inputs["input_dir"].path)
    transcripts_dir = _resolve_transcripts_dir(dirpath)

    # Write one .txt per audio file under transcripts_dir so downstream text_summarization can read them.
    results = model.transcribe_files_in_directory(str(dirpath), str(transcripts_dir))
    result_texts = [
        TextResponse(value=r["result"], title=r["file_path"]) for r in results
    ]

    print(f"Transcription Results: {results}")
    response = BatchTextResponse(
        texts=result_texts,
        transcripts_dir=str(transcripts_dir),
    )
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
