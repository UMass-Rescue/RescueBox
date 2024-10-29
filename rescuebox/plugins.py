from dataclasses import dataclass

import typer
from rb_doc_parser.main import app as rb_doc_parser_app  # type: ignore
from rb_file_utils.main import app as rb_file_utils_app  # type: ignore


@dataclass(frozen=True)
class RescueBoxPlugin:
    app: typer.Typer
    cli_name: str
    full_name: str | None


# Add plugins here
plugins: list[RescueBoxPlugin] = [
    RescueBoxPlugin(rb_file_utils_app, "fs", "File Utils"),
    RescueBoxPlugin(rb_doc_parser_app, "docs", "Docs Utils"),
]
