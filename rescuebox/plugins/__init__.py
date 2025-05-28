from dataclasses import dataclass

import typer
from audio_transcription.main import (
    app as audio_transcription_app,
    APP_NAME as AUDIO_APP_NAME,
)  # type: ignore
from text_summary.main import app as text_summary_app, APP_NAME as TEXT_SUM_APP_NAME  # type: ignore

from age_and_gender_detection.main import app as age_gender_app, APP_NAME as AGE_GENDER_APP_NAME  # type: ignore

# Import plugin modules
from doc_parser.main import app as doc_parser_app  # type: ignore
from file_utils.main import app as file_utils_app  # type: ignore

from video_summarizer.main import (
    app as video_summarizer_app,
    APP_NAME as VIDEO_SUMMARIZER_APP_NAME,
)


@dataclass(frozen=True)
class RescueBoxPlugin:
    app: typer.Typer
    cli_name: str
    full_name: str | None


# Define plugins here (NOT dynamically in main.py)
plugins: list[RescueBoxPlugin] = [
    RescueBoxPlugin(file_utils_app, "fs", "File Utils"),
    RescueBoxPlugin(doc_parser_app, "docs", "Docs Utils"),
    RescueBoxPlugin(
        audio_transcription_app, AUDIO_APP_NAME, "Audio transcription library"
    ),
    RescueBoxPlugin(age_gender_app, AGE_GENDER_APP_NAME, "Age and Gender Classifier"),
    RescueBoxPlugin(text_summary_app, TEXT_SUM_APP_NAME, "Text summarization library"),
    RescueBoxPlugin(
        video_summarizer_app, VIDEO_SUMMARIZER_APP_NAME, "Video summarization library"
    ),
]

# Ensure this module is importable
__all__ = ["plugins"]
