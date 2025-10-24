from dataclasses import dataclass

import typer
from audio_transcription.main import (
    app as audio_transcription_app,
    APP_NAME as AUDIO_APP_NAME,
)  # type: ignore
from text_summary.main import app as text_summary_app, APP_NAME as TEXT_SUM_APP_NAME  # type: ignore
from age_and_gender_detection.main import app as age_gender_app, APP_NAME as AGE_GENDER_APP_NAME  # type: ignore
from deepfake_detection.main import app as deepfake_detection_app, APP_NAME as DEEPFAKE_APP_NAME  # type: ignore

# Import plugin modules
from doc_parser.main import app as doc_parser_app  # type: ignore
from file_utils.main import app as file_utils_app  # type: ignore
from face_detection_recognition.face_match_server import (
    app as face_detection_app,
    APP_NAME as FACE_MATCH_APP_NAME,
)  # type: ignore

ufdr_app = None
try:
    from ufdr_mounter.ufdr_server import app as ufdr_app, APP_NAME as UFDR_APP_NAME  # type: ignore
except EnvironmentError:
    print(
        "Warning: UFDR pre req for mount not available. Hence skipping the UFDR plugin. "
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
        face_detection_app, FACE_MATCH_APP_NAME, "Face Detection and Recognition Tool"
    ),
    RescueBoxPlugin(
        deepfake_detection_app, DEEPFAKE_APP_NAME, "Deepfake Image Detection"
    ),
]

from hello_world.main import app as hello_world_app # type: ignore

if ufdr_app:
    plugins.append(
        RescueBoxPlugin(ufdr_app, UFDR_APP_NAME, "UFDR mount plugin")
    )  # type: ignore

plugins.append(RescueBoxPlugin(hello_world_app, "hello", "Hello World"))


__all__ = ["plugins"]
