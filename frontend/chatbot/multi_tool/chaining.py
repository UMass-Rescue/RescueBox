"""Helpers for chaining prior tool outputs into next-step arguments."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from rb.api.models import InputType, ResponseBody, TaskSchema, TextResponse

from frontend.chatbot.multi_tool.output_path import extract_output_path

logger = logging.getLogger(__name__)


def _find_directory_keys_for_chaining(
    current_schema: TaskSchema, current_arguments: dict[str, Any]
) -> tuple[str | None, str | None]:
    input_dir_key = None
    output_dir_key = None
    for input_schema in current_schema.inputs:
        if input_schema.input_type != InputType.DIRECTORY:
            continue
        key_lower = input_schema.key.lower()
        if "input" in key_lower and "dir" in key_lower:
            input_dir_key = input_schema.key
        if "output" in key_lower and "dir" in key_lower:
            output_dir_key = input_schema.key
    if not input_dir_key:
        for key in current_arguments:
            key_lower = key.lower()
            if "input" in key_lower and ("dir" in key_lower or "dataset" in key_lower):
                input_dir_key = key
                break
    return input_dir_key, output_dir_key


def _apply_default_summarize_output_dir(
    current_arguments: dict[str, Any],
    current_schema: TaskSchema,
    input_dir_key: str,
    output_path: str,
) -> None:
    for inp in current_schema.inputs:
        if inp.input_type != InputType.DIRECTORY:
            continue
        k = inp.key
        if k == input_dir_key:
            continue
        kl = k.lower()
        if "output" in kl and "dir" in kl and not current_arguments.get(k):
            suggested = Path(output_path).parent / "text_summary"
            current_arguments[k] = suggested.as_posix()
            logger.debug(
                "Chained default %s for summarize pipeline: %s",
                k,
                current_arguments[k],
            )
            break


def _inject_file_filter_from_prior_text(
    current_arguments: dict[str, Any], previous_output: ResponseBody
) -> None:
    root = previous_output.root
    if not isinstance(root, TextResponse) or not root.value:
        return
    try:
        parsed = json.loads(root.value)
    except (json.JSONDecodeError, TypeError):
        return
    if isinstance(parsed, dict) and parsed.get("image_summary"):
        raw_paths = parsed.get("files") or []
    elif isinstance(parsed, list):
        raw_paths = parsed
    else:
        raw_paths = []
    file_paths = [p for p in raw_paths if isinstance(p, str)]
    if not file_paths:
        return
    current_arguments["file_filter"] = {"files": [{"path": p} for p in file_paths]}
    logger.info(
        "Chained %d file(s) to file_filter from prior TextResponse",
        len(file_paths),
    )


def chain_output_to_input(
    previous_output: ResponseBody,
    current_arguments: dict[str, Any],
    current_schema: TaskSchema,
) -> dict[str, Any]:
    """Chain prior output path into next-step directory arguments where possible."""
    logger.debug("Attempting to chain output from previous call to current call")
    output_path = extract_output_path(previous_output)
    if not output_path:
        logger.info("No output path found in previous result, skipping chaining")
        return current_arguments

    input_dir_key, output_dir_key = _find_directory_keys_for_chaining(
        current_schema, current_arguments
    )
    if not input_dir_key:
        logger.debug("No input directory field found in schema, skipping chaining")
        return current_arguments

    logger.info("Chaining path '%s' to input '%s'", output_path, input_dir_key)
    current_arguments = current_arguments.copy()
    current_arguments[input_dir_key] = output_path
    current_arguments[output_dir_key] = output_path
    logger.info("Chaining path '%s' to output '%s'", output_path, output_dir_key)
    _apply_default_summarize_output_dir(
        current_arguments, current_schema, input_dir_key, output_path
    )
    _inject_file_filter_from_prior_text(current_arguments, previous_output)
    return current_arguments
