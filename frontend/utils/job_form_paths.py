"""
Helpers for job form input/output directory defaults (e.g. sibling ``outputs`` folder).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from rb.api.models import InputType
except ImportError:
    InputType = None  # type: ignore[misc, assignment]


def suggested_outputs_dir_path(valid_input_dir: str) -> str:
    """Return ``<resolved_input_parent>/outputs`` for a validated input directory path."""
    raw = (valid_input_dir or "").strip()
    if not raw:
        return ""
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return str(p.resolve().parent)


def maybe_autofill_output_dir_field(
    form_widgets: Dict[str, Any],
    output_field_id: str,
    valid_input_dir: str,
) -> None:
    """
    Set the output directory widget to the suggested ``outputs`` path only when the
    output field is still empty (user or ``initial_values`` may have set it already).
    """
    w = form_widgets.get(output_field_id)
    if w is None:
        return
    try:
        cur = (w.value or "").strip()
    except Exception:
        return
    if cur:
        return
    suggested = suggested_outputs_dir_path(valid_input_dir)
    if not suggested:
        return
    try:
        w.set_value(suggested)
    except Exception:
        try:
            w.value = suggested
        except Exception as e:
            logger.debug("Could not autofill output dir %s: %s", output_field_id, e)


def _coerce_input_type(schema: Any) -> Optional[Any]:
    if InputType is None:
        return None
    it = getattr(schema, "input_type", None)
    if it is None:
        return None
    if isinstance(it, InputType):
        return it
    try:
        return InputType(it)
    except Exception:
        return None


def paired_output_directory_field_id(
    inputs_list: List[Any],
    index: int,
) -> Optional[str]:
    """
    For task schemas like ``input_dir`` + ``output_dir`` (or ``input_dataset`` + ``output_file``),
    return the output field id to pre-fill when the input directory validates.

    Used by Describe Images, Text Summarization, Deepfake Detection, and similar plugins.
    """
    if InputType is None:
        return None
    if not inputs_list or index < 0 or index >= len(inputs_list):
        return None
    cur = inputs_list[index]
    if _coerce_input_type(cur) != InputType.DIRECTORY:
        return None
    key = getattr(cur, "key", None)
    if key not in ("input_dir", "input_dataset"):
        return None
    if index + 1 >= len(inputs_list):
        return None
    nxt = inputs_list[index + 1]
    if _coerce_input_type(nxt) != InputType.DIRECTORY:
        return None
    nxt_key = getattr(nxt, "key", None)
    if nxt_key not in ("output_dir", "output_file"):
        return None
    return nxt_key


def suggested_ufdr_mount_folder_path(ufdr_file_path: str) -> str:
    """
    Default mount folder next to the UFDR case layout: ``.../case/inputs/file.ufdr`` →
    ``.../case/outputs`` (parent of the file's directory, then sibling ``outputs``).
    """
    raw = (ufdr_file_path or "").strip()
    if not raw:
        return ""
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return str(p.resolve().parent.parent / "outputs")


def maybe_autofill_ufdr_mount_name_field(
    form_widgets: Dict[str, Any],
    mount_name_field_id: str,
    valid_ufdr_path: str,
) -> None:
    """Set ``mount_name`` text to the suggested ``outputs`` path when still empty."""
    w = form_widgets.get(mount_name_field_id)
    if w is None:
        return
    try:
        cur = (w.value or "").strip()
    except Exception:
        return
    if cur:
        return
    suggested = suggested_ufdr_mount_folder_path(valid_ufdr_path)
    if not suggested:
        return
    try:
        w.set_value(suggested)
    except Exception:
        try:
            w.value = suggested
        except Exception as e:
            logger.debug("Could not autofill UFDR mount_name %s: %s", mount_name_field_id, e)


def paired_ufdr_mount_name_field_id(inputs_list: List[Any], index: int) -> Optional[str]:
    """
    UFDR mounter: ``ufdr_file`` (FILE) then ``mount_name`` (TEXT) → return ``mount_name`` key.
    """
    if InputType is None:
        return None
    if not inputs_list or index < 0 or index >= len(inputs_list):
        return None
    cur = inputs_list[index]
    if getattr(cur, "key", None) != "ufdr_file":
        return None
    if _coerce_input_type(cur) != InputType.FILE:
        return None
    if index + 1 >= len(inputs_list):
        return None
    nxt = inputs_list[index + 1]
    if getattr(nxt, "key", None) != "mount_name":
        return None
    if _coerce_input_type(nxt) != InputType.TEXT:
        return None
    return "mount_name"


def apply_ufdr_mount_autofill_after_inputs_built(
    inputs_list: List[Any],
    form_widgets: Dict[str, Any],
) -> None:
    """
    After all input widgets exist, pre-fill ``mount_name`` if ``ufdr_file`` has a path
    and ``mount_name`` is empty (handles initial_values set before ``mount_name`` exists).
    """
    if not paired_ufdr_mount_name_field_id(inputs_list, 0):
        return
    try:
        ufdr_w = form_widgets.get("ufdr_file")
        if ufdr_w is None:
            return
        p = (ufdr_w.value or "").strip()
    except Exception:
        return
    if not p:
        return
    maybe_autofill_ufdr_mount_name_field(form_widgets, "mount_name", p)
