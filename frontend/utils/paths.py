import logging
from pathlib import Path
from typing import Optional, List, Any, Dict
from rb.api.models import InputType

from frontend.config import DEMO_FOLDERS_BASE
from frontend.utils.exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)


def path_for_ui(value: Any) -> str:
    """Return a normal drive/UNC path string (no Windows ``\\\\?\\`` extended prefix)."""
    s = str(value).strip()
    if s.startswith("\\\\?\\UNC\\"):
        return "\\\\" + s[8:]
    if s.startswith("\\\\?\\"):
        return s[4:]
    return s


def _absolute_path(path: Path) -> Path:
    p = path.expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.absolute()


_COMMON_RASTER_IMAGE_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tiff",
    ".tif",
    ".gif",
    ".heic",
    ".heif",
)


def _resolve_input_path(path_value: Any) -> Path:
    path_str = (
        path_value.get("path") if isinstance(path_value, dict) else str(path_value)
    )
    if not path_str:
        return Path(path_str)
    p = Path(path_str)
    if p.is_absolute() and p.exists():
        return p
    if p.exists():
        return p.absolute()
    try:
        demo_p = DEMO_FOLDERS_BASE / path_str
        if demo_p.exists():
            return demo_p.absolute()
    except UI_RENDER_ERRORS:
        pass
    return p.absolute()


def is_outputs_results_directory(path: str) -> bool:
    if not path:
        return False
    try:
        return Path(path).absolute().name.casefold() == "outputs"
    except UI_RENDER_ERRORS:
        return Path(path).name.casefold() == "outputs"


def suggested_outputs_dir_path(valid_input_dir: str) -> str:
    raw = (valid_input_dir or "").strip()
    if not raw:
        return ""
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return str(p.absolute().parent)


def maybe_autofill_output_dir_field(form_widgets, output_field_id, valid_input_dir):
    w = form_widgets.get(output_field_id)
    if w is None or getattr(w, "value", None):
        return
    suggested = suggested_outputs_dir_path(valid_input_dir)
    if suggested:
        try:
            w.set_value(suggested)
        except UI_RENDER_ERRORS:
            w.value = suggested


def suggested_ufdr_mount_folder_path(ufdr_file_path: str) -> str:
    raw = (ufdr_file_path or "").strip()
    if not raw:
        return ""
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return str(p.absolute().parent.parent / "outputs")


def apply_ufdr_mount_autofill_after_inputs_built(
    form_widgets: Dict, ufdr_file_field_id: str, mount_folder_field_id: str
):
    """Effect helper to link a UFDR file selection to an automatic output path suggestion."""
    ufdr_w = form_widgets.get(ufdr_file_field_id)
    mount_w = form_widgets.get(mount_folder_field_id)
    if not ufdr_w or not mount_w:
        return

    def on_change(e):
        if not mount_w.value:
            suggested = suggested_ufdr_mount_folder_path(e.value)
            if suggested:
                mount_w.set_value(suggested)

    ufdr_w.on_value_change(on_change)


def maybe_autofill_ufdr_mount_name_field(
    form_widgets: Dict, mount_name_field_id: str, ufdr_file_path: str
):
    """Effect helper to pre-fill a UFDR mount point name based on the selected file."""
    w = form_widgets.get(mount_name_field_id)
    if not w or w.value:
        return

    raw = (ufdr_file_path or "").strip()
    if not raw:
        return
    p = Path(raw).name
    name = p.rsplit(".", 1)[0]
    try:
        w.set_value(name)
    except UI_RENDER_ERRORS:
        w.value = name


def _directory_contains_raster_image(
    root: Path, max_files_scanned: int = 12000
) -> bool:
    try:
        resolved = root.expanduser().resolve(strict=False)
        if not resolved.is_dir():
            return False
        scanned = 0
        for p in resolved.rglob("*"):
            if not p.is_file() or p.name.startswith("."):
                continue
            scanned += 1
            if scanned > max_files_scanned:
                return False
            if any(p.name.lower().endswith(s) for s in _COMMON_RASTER_IMAGE_SUFFIXES):
                return True
    except UI_RENDER_ERRORS:
        pass
    return False


def _resolved_existing_directory(initial: Optional[str]) -> Optional[str]:
    if not initial:
        return None
    try:
        p = Path(initial).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        rp = _absolute_path(p)
        if rp.is_dir():
            return path_for_ui(rp)
    except UI_RENDER_ERRORS:
        pass
    return None


def _resolved_file_browser_folder(initial: Optional[str]) -> Optional[str]:
    if not initial:
        return None
    try:
        p = Path(initial).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        rp = _absolute_path(p)
        if rp.is_dir():
            return path_for_ui(rp)
        if rp.is_file():
            return path_for_ui(rp.parent.absolute())
    except UI_RENDER_ERRORS:
        pass
    return None


def _input_schema_directory_requires_raster_image_corpus(
    input_schema: Any,
    all_inputs: List[Any] = None,
    input_index: int = -1,
) -> bool:
    """True when the given directory input likely needs to contain raster images."""
    _ = (all_inputs, input_index)
    label = (input_schema.label or "").strip().lower()
    key = (input_schema.key or "").strip().lower()
    if "image" in label or "photo" in label or "picture" in label:
        return True
    if "image" in key or "photo" in key:
        return True
    return False


def _input_schema_is_text_or_textarea(input_schema: Any) -> bool:
    return input_schema.input_type in (InputType.TEXT, InputType.TEXTAREA)
