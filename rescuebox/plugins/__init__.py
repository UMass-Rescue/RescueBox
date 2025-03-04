from dataclasses import dataclass
import typer

# Import plugin modules
from rb_doc_parser.main import app as rb_doc_parser_app  # type: ignore
from rb_file_utils.main import app as rb_file_utils_app  # type: ignore
from rb_audio_transcription.main import app as rb_audio_transcription_app  # type: ignore
from rb_facematch.main import app as rb_facmatch_app # type: ignore


@dataclass(frozen=True)
class RescueBoxPlugin:
    app: typer.Typer
    cli_name: str
    full_name: str | None


# Define plugins here (NOT dynamically in main.py)
plugins: list[RescueBoxPlugin] = [
    RescueBoxPlugin(rb_file_utils_app, "fs", "File Utils"),
    RescueBoxPlugin(rb_doc_parser_app, "docs", "Docs Utils"),
    RescueBoxPlugin(rb_audio_transcription_app, "audio", "Audio transcription library"),
    RescueBoxPlugin(rb_facmatch_app, "facematch", "Facematch plugin"),
]

# Ensure this module is importable
__all__ = ["plugins"]
