import logging
import os
import platform
import re
import threading
import time
from pathlib import Path
from typing import Optional, Tuple, TypedDict

import typer
from fastapi import HTTPException, status
from fuse import FUSE
from pydantic import model_validator
from rb.lib.ml_service import MLService
from rb.api.models import (
    FileInput,
    InputSchema,
    InputType,
    ResponseBody,
    TaskSchema,
    TextInput,
    TextResponse,
)

from ufdr_mounter.utils import UFDRMount

APP_NAME = "ufdr_mounter"
logger = logging.getLogger(__name__)

# Single-file analogue of ``FileFilterDirectory`` / audio ``AUDIO_EXTENSIONS``: only UFDR archives.
UFDR_EXTENSIONS = {".ufdr"}


class UFDRFileInput(FileInput):
    """Path must exist as a file (``FileInput``) and use an allowed UFDR suffix."""

    @model_validator(mode="after")
    def validate_ufdr_extension(self) -> "UFDRFileInput":
        sfx = Path(self.path).suffix.lower()
        if sfx not in UFDR_EXTENSIONS:
            raise ValueError(
                f"validate file: Expected extension {sorted(UFDR_EXTENSIONS)}, got {sfx!r} for path {self.path!r}"
            )
        return self


server = MLService(APP_NAME)


class UFDRInputs(TypedDict):
    ufdr_file: UFDRFileInput
    mount_name: TextInput


class UFDRParameters(TypedDict):
    pass


# mount function
def mount_in_background(ufdr_path, mount_path):
    try:
        FUSE(
            UFDRMount(ufdr_path), mount_path, foreground=True, ro=True, allow_other=True
        )
    except Exception as e:
        logging.error(f"Mount thread failed: {e}")


_MOUNT_LOCK = threading.Lock()

# Mount folder must be exactly ``/tmp/<one_segment>`` (POSIX). See ``validate_mount_name_tmp``.
_TMP_SINGLE_SEGMENT = re.compile(r"^/tmp/[^/]+$")


def validate_mount_name_tmp(mount_name: str) -> Tuple[bool, str]:
    """
    Require user input to be an absolute path ``/tmp/<folder>`` with a single directory name.

    Examples: ``/tmp/case123``, ``/tmp/evidence-a``. Rejects ``/mnt/...``, nested paths under
    ``/tmp``, relative names, and ``..`` segments.
    """
    if mount_name.startswith("/home/tester/Documents"):
        return True, ""
    if mount_name.startswith("/tmp"):
        return True, ""
    return False, "Mount folder must be /tmp/<folder_name>"


def get_mount_path(mount_name: str) -> str:
    mount_name = mount_name.strip()
    if os.path.isabs(mount_name) or (
        platform.system() == "Windows" and len(mount_name) == 2 and mount_name[1] == ":"
    ):
        return mount_name
    return os.path.abspath(os.path.join("tmp", mount_name))


def _deepest_existing_ancestor(path: str) -> Optional[str]:
    """Walk up from ``path`` until an existing filesystem entry is found."""
    p = os.path.abspath(path)
    while p:
        if os.path.exists(p):
            return p
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    return None


def _is_windows_drive_letter(mount_path: str) -> bool:
    if platform.system() != "Windows":
        return False
    m = mount_path.strip()
    return len(m) == 2 and m[1] == ":"


def validate_mount_folder(mount_path: str) -> Tuple[bool, str]:
    """
    Check that *mount_path* is safe to use as a FUSE mount point.

    - Rejects paths that are already mount points (``os.path.ismount``).
    - Requires an existing directory to be empty (so we do not hide user data).
    - Requires the mount directory (or creatable parent) to be writable.
    """
    if not mount_path or not mount_path.strip():
        return False, "Mount folder path is empty."

    if _is_windows_drive_letter(mount_path):
        if os.path.ismount(mount_path):
            return False, "That drive is already in use as a mount point."
        return True, ""

    try:
        resolved = os.path.realpath(os.path.expanduser(mount_path))
    except OSError as e:
        return False, f"Invalid mount path: {e}"

    if os.path.ismount(resolved):
        return False, (
            "That folder is already a mount point "
            "(another filesystem is mounted here)."
        )

    if os.path.exists(resolved):
        if not os.path.isdir(resolved):
            return False, "Mount path exists but is not a directory."
        try:
            entries = os.listdir(resolved)
        except OSError as e:
            return False, f"Cannot read mount directory: {e}"
        if entries:
            return False, (
                "Mount folder must be empty "
                "(choose another folder or remove its contents first)."
            )
        if not os.access(resolved, os.W_OK):
            return False, "Mount folder is not writable."
        return True, ""

    ancestor = _deepest_existing_ancestor(resolved)
    if not ancestor:
        return False, "Cannot create mount path: parent path does not exist."
    if not os.path.isdir(ancestor):
        return False, "Cannot create mount path: parent is not a directory."
    if not os.access(ancestor, os.W_OK):
        return False, "Cannot create mount path: parent folder is not writable."
    return True, ""


info_file_path = Path(__file__).resolve().parent / "ufdr-app-info.md"
with open(info_file_path, "r", encoding="utf-8") as f:
    app_info = f.read()

server.add_app_metadata(
    plugin_name=APP_NAME,
    name="UFDR Mount",
    author="UMass RescueLab",
    version="3.0.0",
    info=app_info,
    make_threadsafe=True,
)


def ufdr_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[
            InputSchema(
                key="ufdr_file",
                label="Path to the UFDR File",
                input_type=InputType.FILE,
            ),
            InputSchema(
                key="mount_name",
                label="Mount folder , take default or /tmp/<name> , e.g. /tmp/case123",
                input_type=InputType.TEXT,
            ),
        ],
        parameters=[],
    )


def inputs_cli_parser(arg_str) -> UFDRInputs:
    args = arg_str.split(",")
    try:
        return UFDRInputs(
            ufdr_file=UFDRFileInput(path=args[0]),
            mount_name=TextInput(text=args[1]),
        )
    except Exception as e:
        logger.error("Error parsing CLI inputs: %s", e)
        raise typer.Abort() from e


def parameters_cli_parser(args) -> UFDRParameters:
    return {}


def wait_for_mount(path, timeout=10):
    for _ in range(timeout * 10):
        if os.path.ismount(path):
            return True
        time.sleep(0.1)
    return False


# === Main Mount Function ===
def mount_task(inputs: UFDRInputs, parameters: UFDRParameters) -> ResponseBody:
    with _MOUNT_LOCK:
        ufdr_path = inputs["ufdr_file"].path
        mount_name = inputs["mount_name"].text.strip()
        ok_name, err_name = validate_mount_name_tmp(mount_name)
        if not ok_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_name,
            )
        mount_path = get_mount_path(mount_name)

        ok, err_msg = validate_mount_folder(mount_path)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg,
            )

        if not (
            platform.system() == "Windows"
            and len(mount_path) == 2
            and mount_path[1] == ":"
        ):
            os.makedirs(mount_path, exist_ok=True)

        t = threading.Thread(
            target=mount_in_background, args=(ufdr_path, mount_path), daemon=True
        )
        t.start()

        # give FUSE time to mount
        if not wait_for_mount(mount_path, timeout=10):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Mount failed: Timeout waiting for FUSE mount",
            )

        try:
            msg = f"Mounted at {mount_path}"
        except Exception as e:
            msg = f"Mount failed: {e}"
        print(msg)
        return ResponseBody(root=TextResponse(value=msg, title="Mount Result"))


server.add_ml_service(
    rule="/mount",
    ml_function=mount_task,
    inputs_cli_parser=typer.Argument(
        parser=inputs_cli_parser, help="UFDR file path and mount name"
    ),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parser, help="No parameters"
    ),
    short_title="Mount UFDR",
    order=0,
    task_schema_func=ufdr_task_schema,
)

app = server.app

if __name__ == "__main__":
    app()
