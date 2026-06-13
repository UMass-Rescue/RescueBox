"""Map task schemas and tool arguments to form-friendly values."""

import logging
from typing import Dict, Any, Union
from rb.api.models import TaskSchema, InputType
from frontend.chatbot.utils import normalize_arguments

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _unwrap_input_value_for_form(value: Any, wrapper: str) -> Union[str, Any]:
    """
    Tool args and API bodies sometimes use plain strings; other times ``{'text': ...}``
    or ``{'path': ...}``. If we ``str()`` a dict we get ``\"{'text': '/tmp/x'}\"``, which
    breaks TextInput and re-wraps badly on submit (UFDR ``mount_name``).
    """
    if isinstance(value, dict):
        if wrapper == "path":
            if "path" in value and value["path"] is not None:
                return str(value["path"])
        else:
            if "text" in value and value["text"] is not None:
                return str(value["text"])
            if "path" in value and value["path"] is not None:
                return str(value["path"])
    return value


def convert_arguments_to_initial_values(
    arguments: Dict[str, Any], task_schema: TaskSchema, endpoint: str = ""
) -> Dict[str, Any]:
    """
    Convert tool call arguments to initial_values format for form pre-filling.
    Extracted utility from core to keep core thin.
    """
    logger.debug("Converting arguments to initial values for endpoint: %s", endpoint)
    logger.debug("Input arguments keys: %s", list(arguments.keys()))

    normalized_args = normalize_arguments(arguments, endpoint)
    logger.debug("Normalized arguments keys: %s", list(normalized_args.keys()))

    initial_values = {"inputs": {}, "parameters": {}}
    path_types = {InputType.DIRECTORY, InputType.FILE}

    for input_schema in task_schema.inputs:
        if (key := input_schema.key) in normalized_args:
            wrapper = "path" if input_schema.input_type in path_types else "text"
            raw = normalized_args[key]
            inner = _unwrap_input_value_for_form(raw, wrapper)
            initial_values["inputs"][key] = {wrapper: str(inner)}

    for param_schema in task_schema.parameters:
        if (key := param_schema.key) in normalized_args:
            initial_values["parameters"][key] = normalized_args[key]

    # Pipeline-only keys (e.g. file_filter) may be omitted from public task_schema but must
    # round-trip through the form so summarize → search-text passes explicit transcript paths.
    ff = normalized_args.get("file_filter")
    if isinstance(ff, dict) and ff.get("files"):
        initial_values["inputs"]["file_filter"] = ff

    logger.debug(
        "Conversion complete: %d inputs, %d parameters",
        len(initial_values["inputs"]),
        len(initial_values["parameters"]),
    )
    return initial_values
