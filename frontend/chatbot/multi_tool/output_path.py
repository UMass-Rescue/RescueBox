"""Output-path extraction helpers for chained multi-tool calls."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from rb.api.models import (
    BatchDirectoryResponse,
    BatchFileResponse,
    BatchTextResponse,
    DirectoryResponse,
    FileResponse,
    ResponseBody,
    TextResponse,
)

from frontend.chatbot.exceptions import CHATBOT_ERRORS

logger = logging.getLogger(__name__)


def _path_from_directory_path(path: str) -> str:
    p = Path(path)
    return p.parent.as_posix() if p.is_file() else p.as_posix()


def _path_from_batch_text(root: BatchTextResponse) -> Optional[str]:
    if not getattr(root, "transcripts_dir", None):
        return None
    td = Path(root.transcripts_dir).as_posix()
    logger.debug("Extracted transcripts_dir from BatchTextResponse: %s", td)
    return td


def _path_from_text_mount_message(value: str) -> Optional[str]:
    vm = (value or "").strip()
    if not vm.lower().startswith("mounted at "):
        return None
    mp = vm[len("Mounted at ") :].strip()
    if not mp:
        return None
    files_root = Path(mp.rstrip("/")) / "files"
    logger.debug(
        "Extracted UFDR files root from mount message: %s",
        files_root.as_posix(),
    )
    return files_root.as_posix()


def _path_from_text_json_file_list(value: str) -> Optional[str]:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None
    file_list = None
    if isinstance(parsed, dict) and parsed.get("image_summary"):
        file_list = parsed.get("files")
    elif isinstance(parsed, list):
        file_list = parsed
    if not file_list or not isinstance(file_list, list):
        return None
    first_path = file_list[0]
    if not isinstance(first_path, str):
        return None
    output_path = Path(first_path).parent.as_posix()
    logger.debug(
        "Extracted output path from TextResponse (file list): %s",
        output_path,
    )
    return output_path


def _path_from_text_response(root: TextResponse) -> Optional[str]:
    if not root.value:
        return None
    mount = _path_from_text_mount_message(root.value)
    if mount:
        return mount
    return _path_from_text_json_file_list(root.value)


def _path_from_response_root(root: Any) -> Optional[str]:
    if isinstance(root, BatchTextResponse):
        return _path_from_batch_text(root)
    if isinstance(root, TextResponse):
        return _path_from_text_response(root)
    if isinstance(root, BatchDirectoryResponse) and root.directories:
        output_path = root.directories[0].path
        logger.debug(
            "Extracted output path from BatchDirectoryResponse: %s", output_path
        )
        return _path_from_directory_path(output_path)
    if isinstance(root, DirectoryResponse):
        logger.debug("Extracted output path from DirectoryResponse: %s", root.path)
        return _path_from_directory_path(root.path)
    if isinstance(root, BatchFileResponse) and root.files:
        output_path = Path(root.files[0].path).parent
        logger.debug("Extracted output path from BatchFileResponse: %s", output_path)
        return output_path.as_posix()
    if isinstance(root, FileResponse):
        output_path = Path(root.path).parent
        logger.debug("Extracted output path from FileResponse: %s", output_path)
        return output_path.as_posix()
    return None


def extract_output_path(response_body: ResponseBody) -> Optional[str]:
    """Extract output directory/path from a plugin ``ResponseBody``."""
    try:
        path = _path_from_response_root(response_body.root)
        if path:
            return path
        logger.debug("Could not extract output path from response")
        return None
    except CHATBOT_ERRORS as e:
        logger.warning("Error extracting output path: %s", str(e))
        return None
