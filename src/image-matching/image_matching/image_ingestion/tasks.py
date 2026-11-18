from pathlib import Path
from typing import TypedDict

from image_matching import archive_store
from image_matching.hashing.essay import ESSAY_MAX_WORDS, ensure_essay_model
from image_matching.hashing.hashers import (
    HASH_OPTIONS,
    fill_missing,
    sha256_file,
)
from rb.api.database import engine
from rb.api.models import (
    DirectoryInput,
    EnumParameterDescriptor,
    EnumVal,
    InputSchema,
    InputType,
    IntParameterDescriptor,
    ParameterSchema,
    ResponseBody,
    TaskSchema,
    TextParameterDescriptor,
    TextResponse,
)
from sqlmodel import Session

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

HASH_LABELS: dict[str, tuple[str, str]] = {
    "md5": ("MD5 hash", "Fast, common means of finding exact matches"),
    "pdq": ("PDQ hash", "Relatively fast; enables deduplication"),
    "semantic": (
        "Semantic hash",
        "Moderately fast to slow; enables fuzzy matching",
    ),
    "essay": (
        "Essay hash",
        "Slow. Essay hashes will be sent to the UMass Safe Matching service "
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
    max_essay_words: int


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


def _max_essay_words() -> ParameterSchema:
    return ParameterSchema(
        key="max_essay_words",
        label="Max essay words",
        subtitle=(
            f"Suggested max {ESSAY_MAX_WORDS}; more words make essays slower. "
            "Applies only to new essays"
        ),
        value=IntParameterDescriptor(default=ESSAY_MAX_WORDS),
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
            _max_essay_words(),
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


def _selected_hashes(parameters: IngestParameters) -> list[str]:
    return [
        hash_name
        for option, hash_names in HASH_OPTIONS.items()
        if parameters[option] == "yes"
        for hash_name in hash_names
    ]


def _image_paths(folder: Path) -> list[str]:
    return sorted(
        str(path)
        for path in folder.iterdir()
        if path.suffix.lower() in IMAGE_EXTENSIONS
    )


def _ingest(
    session: Session,
    label: str,
    description: str,
    paths: list[str],
    selected: list[str],
    max_essay_words: int,
) -> None:
    sha256s = {path: sha256_file(path) for path in paths}
    first_path = {sha256: path for path, sha256 in reversed(list(sha256s.items()))}
    for sha256, path in first_path.items():
        record = archive_store.find_or_create_file(session, sha256)
        fill_missing(record, path, selected, max_essay_words)
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
        paths = _image_paths(folder)
        _ingest(
            session,
            label,
            parameters["description"],
            paths,
            selected,
            int(parameters["max_essay_words"]),
        )
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
        taken = archive_store.find_archive(session, new_label)
        if taken is not None and taken is not archive:
            return _label_taken(new_label)
        archive_store.rename_archive(session, archive, new_label)
        session.commit()
    return _text_result("Archive renamed", f"Renamed '{old_label}' to '{new_label}'.")


def ingest_inputs_cli_parse(value: str) -> IngestInputs:
    return IngestInputs(input_dir=DirectoryInput(path=value.strip()))


def ingest_parameters_cli_parse(value: str) -> IngestParameters:
    label, description, md5, pdq, semantic, essay, max_essay_words = value.split("|")
    return IngestParameters(
        label=label,
        description=description,
        md5=md5,
        pdq=pdq,
        semantic=semantic,
        essay=essay,
        max_essay_words=int(max_essay_words),
    )


def no_inputs_cli_parse(_value: str) -> NoInputs:
    return {}


def delete_parameters_cli_parse(value: str) -> DeleteParameters:
    label, retain_hashes = value.split(",")
    return DeleteParameters(label=label, retain_hashes=retain_hashes)


def rename_parameters_cli_parse(value: str) -> RenameParameters:
    old_label, new_label = value.split(",")
    return RenameParameters(old_label=old_label, new_label=new_label)
