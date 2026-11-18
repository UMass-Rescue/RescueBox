from pathlib import Path

import typer
from image_matching.image_ingestion.tasks import (
    delete_archive,
    delete_parameters_cli_parse,
    delete_task_schema,
    ingest_images,
    ingest_inputs_cli_parse,
    ingest_parameters_cli_parse,
    ingest_task_schema,
    no_inputs_cli_parse,
    rename_archive,
    rename_parameters_cli_parse,
    rename_task_schema,
)
from rb.lib.ml_service import MLService

APP_NAME = "image_matching"
server = MLService(APP_NAME)

server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Image Ingestion",
    author="UMass RescueLab",
    version="1.0.0",
    info=(
        Path(__file__).resolve().parent / "image_ingestion" / "app-info.md"
    ).read_text(encoding="utf-8"),
    gpu=True,
)

server.add_ml_service(
    rule="/ingest_images",
    ml_function=ingest_images,
    inputs_cli_parser=typer.Argument(
        parser=ingest_inputs_cli_parse, help="Folder of images"
    ),
    parameters_cli_parser=typer.Argument(
        parser=ingest_parameters_cli_parse,
        help="label|description|md5|pdq|semantic|essay|max_essay_words (hashes yes|no)",
    ),
    short_title="Ingest Images",
    order=0,
    task_schema_func=ingest_task_schema,
)

server.add_ml_service(
    rule="/delete_archive",
    ml_function=delete_archive,
    inputs_cli_parser=typer.Argument(parser=no_inputs_cli_parse, help="Unused"),
    parameters_cli_parser=typer.Argument(
        parser=delete_parameters_cli_parse, help="label,retain_hashes (yes|no)"
    ),
    short_title="Delete Archive",
    order=1,
    task_schema_func=delete_task_schema,
)

server.add_ml_service(
    rule="/rename_archive",
    ml_function=rename_archive,
    inputs_cli_parser=typer.Argument(parser=no_inputs_cli_parse, help="Unused"),
    parameters_cli_parser=typer.Argument(
        parser=rename_parameters_cli_parse, help="old_label,new_label"
    ),
    short_title="Rename Archive",
    order=2,
    task_schema_func=rename_task_schema,
)

app = server.app

if __name__ == "__main__":
    app()
