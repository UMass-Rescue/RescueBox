import logging
from pathlib import Path
from typing import TypedDict

import typer
from image_ingestion import archive_store
from image_ingestion.hashers import HASH_OPTIONS, fill_missing, sha256_file
from image_similarity.main import _collect_image_paths
from rb.api.database import engine
from rb.api.models import (
    DirectoryInput,
    EnumParameterDescriptor,
    EnumVal,
    InputSchema,
    InputType,
    ParameterSchema,
    ResponseBody,
    TaskSchema,
    TextParameterDescriptor,
    TextResponse,
)
from rb.lib.ml_service import MLService
from rb.safe_matching_common.essay import ensure_essay_model
from sqlmodel import Session

logger = logging.getLogger(__name__)

APP_NAME = "image_ingestion"
server = MLService(APP_NAME)

HASH_LABELS: dict[str, tuple[str, str]] = {
    "md5": ("MD5 hash", "Fast, common means of finding exact matches"),
    "pdq": ("PDQ hash", "Relatively fast; enables deduplication"),
    "semantic": (
        "Semantic hash",
        "Moderately fast to slow; enables fuzzy matching",
    ),
    "essay": (
        "Essay hash",
        "Slow. Essay hashes will be sent to the UMass Semantic Matching API "
        "(not yet being done)",
    ),
}


class IngestInputs(TypedDict):
    input_dir: DirectoryInput


class IngestParameters(TypedDict):
    label: str
    description: str
    md5: str
    pdq: str
    semantic: str
    essay: str


class NoInputs(TypedDict):
    pass


class DeleteParameters(TypedDict):
    label: str
    retain_hashes: str


class RenameParameters(TypedDict):
    old_label: str
    new_label: str


def _yes_no() -> EnumParameterDescriptor:
    return EnumParameterDescriptor(
        enum_vals=[EnumVal(key="yes", label="Yes"), EnumVal(key="no", label="No")],
        default="yes",
    )


def _text(key: str, label: str, subtitle: str = "") -> ParameterSchema:
    return ParameterSchema(
        key=key,
        label=label,
        subtitle=subtitle,
        value=TextParameterDescriptor(default=""),
    )


def ingest_task_schema() -> TaskSchema:
    hash_parameters = [
        ParameterSchema(key=key, label=label, subtitle=subtitle, value=_yes_no())
        for key, (label, subtitle) in HASH_LABELS.items()
    ]
    return TaskSchema(
        inputs=[
            InputSchema(
                key="input_dir",
                label="Folder of images to ingest",
                input_type=InputType.DIRECTORY,
            )
        ],
        parameters=[
            _text("label", "Investigation label", "Defaults to the folder name"),
            _text("description", "Description", "Case details, survivor information"),
            *hash_parameters,
        ],
    )


def delete_task_schema() -> TaskSchema:
    retain = ParameterSchema(
        key="retain_hashes",
        label="Retain hashes in the database",
        subtitle="Keeping them makes loading faster if the original data is loaded again",
        value=_yes_no(),
    )
    return TaskSchema(
        inputs=[],
        parameters=[_text("label", "Investigation label of the archive"), retain],
    )


def rename_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[],
        parameters=[
            _text("old_label", "Current investigation label"),
            _text("new_label", "New investigation label"),
        ],
    )


server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Image Ingestion",
    author="UMass RescueLab",
    version="1.0.0",
    info=(Path(__file__).resolve().parent / "app-info.md").read_text(encoding="utf-8"),
    gpu=True,
)


def _selected_hashes(parameters: IngestParameters) -> list[str]:
    return [
        hash_name
        for option, hash_names in HASH_OPTIONS.items()
        if parameters[option] == "yes"
        for hash_name in hash_names
    ]


def _ingest(
    session: Session,
    label: str,
    description: str,
    paths: list[str],
    selected: list[str],
) -> None:
    sha256s = {path: sha256_file(path) for path in paths}
    first_path = {sha256: path for path, sha256 in reversed(list(sha256s.items()))}
    for sha256, path in first_path.items():
        record = archive_store.find_or_create_file(session, sha256)
        fill_missing(record, path, selected)
        if "essay" in selected:
            logger.info("Essay for %s: %s", Path(path).name, record.essay)
        session.commit()
    archive = archive_store.create_archive(session, label, description)
    archive_store.link_files(session, archive, sha256s)
    session.commit()


def ingest_images(inputs: IngestInputs, parameters: IngestParameters) -> ResponseBody:
    folder = Path(inputs["input_dir"].path)
    label = parameters["label"] or folder.name
    selected = _selected_hashes(parameters)
    with Session(engine) as session:
        if archive_store.find_archive(session, label) is not None:
            return _label_taken(label)
        if "essay" in selected:
            ensure_essay_model()
        paths = _collect_image_paths(str(folder))
        _ingest(session, label, parameters["description"], paths, selected)
    message = f"Archive '{label}': {len(paths)} files."
    return _text_result("Ingestion complete", message)


def _text_result(title: str, message: str) -> ResponseBody:
    return ResponseBody(root=TextResponse(value=message, title=title))


def _not_found(label: str) -> ResponseBody:
    return _text_result("Archive not found", f"No archive has the label '{label}'.")


def _label_taken(label: str) -> ResponseBody:
    return _text_result(
        "Label already in use", f"An archive with the label '{label}' already exists."
    )


def delete_archive(inputs: NoInputs, parameters: DeleteParameters) -> ResponseBody:
    label = parameters["label"]
    retain = parameters["retain_hashes"] == "yes"
    with Session(engine) as session:
        archive = archive_store.find_archive(session, label)
        if archive is None:
            return _not_found(label)
        removed = archive_store.delete_archive(session, archive, retain)
        session.commit()
    return _text_result(
        "Archive deleted", f"Deleted archive '{label}' ({removed} files)."
    )


def rename_archive(inputs: NoInputs, parameters: RenameParameters) -> ResponseBody:
    old_label, new_label = parameters["old_label"], parameters["new_label"]
    with Session(engine) as session:
        archive = archive_store.find_archive(session, old_label)
        if archive is None:
            return _not_found(old_label)
        if archive_store.find_archive(session, new_label) is not None:
            return _label_taken(new_label)
        archive_store.rename_archive(session, archive, new_label)
        session.commit()
    return _text_result("Archive renamed", f"Renamed '{old_label}' to '{new_label}'.")


def ingest_inputs_cli_parse(value: str) -> IngestInputs:
    return IngestInputs(input_dir=DirectoryInput(path=value.strip()))


def ingest_parameters_cli_parse(value: str) -> IngestParameters:
    label, description, md5, pdq, semantic, essay = value.split("|")
    return IngestParameters(
        label=label,
        description=description,
        md5=md5,
        pdq=pdq,
        semantic=semantic,
        essay=essay,
    )


def no_inputs_cli_parse(_value: str) -> NoInputs:
    return {}


def delete_parameters_cli_parse(value: str) -> DeleteParameters:
    label, retain_hashes = value.split(",")
    return DeleteParameters(label=label, retain_hashes=retain_hashes)


def rename_parameters_cli_parse(value: str) -> RenameParameters:
    old_label, new_label = value.split(",")
    return RenameParameters(old_label=old_label, new_label=new_label)


server.add_ml_service(
    rule="/ingest_images",
    ml_function=ingest_images,
    inputs_cli_parser=typer.Argument(
        parser=ingest_inputs_cli_parse, help="Folder of images"
    ),
    parameters_cli_parser=typer.Argument(
        parser=ingest_parameters_cli_parse,
        help="label|description|md5|pdq|semantic|essay (each yes|no)",
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
