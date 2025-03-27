"""audio transcribe plugin"""
import logging
import sys
from pathlib import Path
from typing import Annotated, Any, Dict, List

import typer
from fastapi import Body, Depends, HTTPException
from rb.api.models import (API_APPMETDATA, API_ROUTES, PLUGIN_SCHEMA_SUFFIX,
                           BatchTextResponse, DirectoryInput, ResponseBody,
                           TextResponse)
from rb.lib.abstract_parser import AbstractParser
from rb_audio_transcription.model import AudioTranscriptionModel

logger = logging.getLogger(__name__)

app = typer.Typer()
model = AudioTranscriptionModel()

info_file_path = Path("app-info.md")


class AudioTranscriptionParser(AbstractParser):
    """
    Implementation of AbstractParser for Audio Transcription.
    """

    def __init__(self):
        super().__init__(
            name="Audio Transcription",
            version="2.0.0",
            author="RescueBox Team",
            description="A parser for transcribing audio files.",
        )
        self.validator_type = "audio_validator"

    @property
    def routes(self) -> List[Dict[str, Any]]:
        """Defines the available API routes for this parser."""
        return [
            {
                "task_schema": f'/audio/task{PLUGIN_SCHEMA_SUFFIX}',
                "run_task": "/audio/transcribe",
                "short_title": "audio transcribe",
                "order": 0,
            }
        ]

    @property
    def metadata(self) -> Dict[str, Any]:
        """Overrides metadata to provide additional info."""
        return {
            **super().metadata,
            "supported_formats": ["wav", "mp3", "flac"],
            "license": "MIT",
        }

    def validate_inputs(self, inputs: DirectoryInput):
        """
        Validates that the input directory exists and has files.
        """
        try:
            logger.debug("Validating inputs...")
            dirpath = inputs.path
            files = [file for file in dirpath.iterdir() if file.is_file()]

            if len(files) < 1:
                raise HTTPException(status_code=400, detail="No files in given directory for transcription.")

            logger.debug("Validation successful.")
            return inputs
        except Exception as e:
            logger.error(f"Invalid path inputs: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid path inputs for transcription: {e}")

    def cli_parser(self, path: str):
        """
        Parses CLI input path into a Pydantic object.
        """
        try:
            logger.debug(f"Parsing CLI input path: {path}")
            return DirectoryInput(path=path)
        except Exception as e:
            logger.error(f"Error parsing CLI input: {e}")
            raise typer.Abort()


audio_parser = AudioTranscriptionParser()

def is_running_in_fastapi():
    """Detect if the app is running inside FastAPI instead of CLI."""
    return "uvicorn" in sys.modules

@app.command(API_APPMETDATA)
def app_metadata():
    """Return metadata for the current parser."""
    data = audio_parser.metadata or {}  

    if is_running_in_fastapi():
        return data
    
    typer.echo(data)


@app.command(API_ROUTES)
def routes():
    """Return routes for the current parser."""
    data = audio_parser.routes or {}  # Prevent returning `None`

    if is_running_in_fastapi():
        return data  # Return dict, FastAPI will convert it to JSON automatically
    
    typer.echo(data)  # CLI Mode → Print JSON





@app.command('transcribe')
def transcribe(
    inputs: Annotated[
        DirectoryInput,
        typer.Argument(parser=audio_parser.cli_parser, help="Input directory path"),
        Body(embed=True),
        Depends(audio_parser.validate_inputs)
    ]
) -> ResponseBody:
    """Transcribe audio files"""

    logger.debug("Processing transcription...")
    dirpath = inputs.path

    results = model.transcribe_files_in_directory(dirpath)
    result_texts = [
        TextResponse(value=r["result"], title=r["file_path"]) for r in results
    ]

    logger.info(f"Transcription Results: {result_texts}")
    response = BatchTextResponse(texts=result_texts)
    return ResponseBody(root=response)


if __name__ == "__main__":
    app()
