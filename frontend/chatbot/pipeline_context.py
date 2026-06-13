"""Shared helpers for resolving pipeline context across chat entry points."""

from __future__ import annotations

import logging
from typing import Any, Optional

from rb.api.models import InputType, ResponseBody

from frontend.chatbot.multi_tool_handler import extract_output_path
from frontend.database import get_job_db
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)


def find_input_directory_key(task_schema) -> str | None:
    """Find best input directory field in a task schema."""
    for input_schema in task_schema.inputs:
        if input_schema.input_type == InputType.DIRECTORY:
            key_lower = input_schema.key.lower()
            if "input" in key_lower and "dir" in key_lower:
                return input_schema.key
    for input_schema in task_schema.inputs:
        if input_schema.input_type == InputType.DIRECTORY:
            return input_schema.key
    return None


def get_pipeline_output_path(pipeline_job_id: Optional[str]) -> Optional[str]:
    """Resolve output path from a previously completed pipeline job id."""
    if not pipeline_job_id:
        return None
    try:
        job = get_job_db().get_job_by_uid_sync(pipeline_job_id)
        if not job or not job.response:
            return None
        response_body = job.response
        if not isinstance(response_body, ResponseBody):
            response_body = ResponseBody(**response_body)
        return extract_output_path(response_body)
    except UI_RENDER_ERRORS as e:
        logger.error("Error resolving pipeline output path: %s", e)
        return None


def inject_pipeline_path(
    arguments: Any, task_schema, pipeline_job_id: Optional[str]
) -> dict:
    """Inject resolved pipeline output path into the task input directory argument."""
    merged = arguments.copy() if arguments else {}
    output_path = get_pipeline_output_path(pipeline_job_id)
    if not output_path:
        return merged
    input_dir_key = find_input_directory_key(task_schema)
    if not input_dir_key:
        return merged
    merged[input_dir_key] = output_path
    logger.info(
        "Pipelining: injected output path '%s' into '%s'",
        output_path,
        input_dir_key,
    )
    return merged
