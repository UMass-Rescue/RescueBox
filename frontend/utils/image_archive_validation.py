from pathlib import Path

import httpx

from frontend.config import API_TIMEOUT, BACKEND_URL

INGEST_ENDPOINT = "image_matching/ingest_images"
DELETE_ENDPOINT = "image_matching/delete_archive"
RENAME_ENDPOINT = "image_matching/rename_archive"
ARCHIVE_LABELS_PATH = "/image_matching/archive_labels"

ARCHIVE_LABEL_PARAMETER_KEYS = frozenset({"label", "old_label"})
CHOOSE_ARCHIVE = "Choose an archive from the list."


def fetch_archive_labels() -> list[str]:
    response = httpx.post(f"{BACKEND_URL}{ARCHIVE_LABELS_PATH}", timeout=API_TIMEOUT)
    response.raise_for_status()
    return response.json()


def use_archive_label_picker(endpoint: str | None, param_key: str) -> bool:
    return endpoint in (DELETE_ENDPOINT, RENAME_ENDPOINT) and (
        param_key in ARCHIVE_LABEL_PARAMETER_KEYS
    )


def _param(form_data: dict, key: str) -> str:
    return str((form_data.get("parameters") or {}).get(key) or "").strip()


def _ingest_label(form_data: dict) -> str:
    path = str(form_data["inputs"]["input_dir"]["path"]).strip()
    return _param(form_data, "label") or Path(path).name


def _taken(label: str) -> str:
    return f"An archive with the label '{label}' already exists."


def _ingest_errors(form_data: dict, labels: list[str]) -> dict[str, str]:
    label = _ingest_label(form_data)
    return {"label": _taken(label)} if label in labels else {}


def _delete_errors(form_data: dict) -> dict[str, str]:
    return {} if _param(form_data, "label") else {"label": CHOOSE_ARCHIVE}


def _rename_errors(form_data: dict, labels: list[str]) -> dict[str, str]:
    old_label = _param(form_data, "old_label")
    new_label = _param(form_data, "new_label")
    errors: dict[str, str] = {}
    if not old_label:
        errors["old_label"] = CHOOSE_ARCHIVE
    if not new_label:
        errors["new_label"] = "Enter a new investigation label."
    elif new_label != old_label and new_label in labels:
        errors["new_label"] = _taken(new_label)
    return errors


def validate_image_archive_form(form_data: dict, endpoint: str) -> dict[str, str]:
    if endpoint == DELETE_ENDPOINT:
        return _delete_errors(form_data)
    if endpoint == INGEST_ENDPOINT:
        return _ingest_errors(form_data, fetch_archive_labels())
    if endpoint == RENAME_ENDPOINT:
        return _rename_errors(form_data, fetch_archive_labels())
    return {}
