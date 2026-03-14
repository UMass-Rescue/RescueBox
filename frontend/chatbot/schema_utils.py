import logging
from typing import Dict, Any
from rb.api.models import TaskSchema, InputType
from frontend.chatbot.utils import normalize_arguments

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def convert_arguments_to_initial_values(arguments: Dict[str, Any], task_schema: TaskSchema, endpoint: str = "") -> Dict[str, Any]:
    """
    Convert tool call arguments to initial_values format for form pre-filling.
    Extracted utility from core to keep core thin.
    """
    logger.info("Converting arguments to initial values for endpoint: %s", endpoint)
    logger.debug("Input arguments keys: %s", list(arguments.keys()))

    normalized_args = normalize_arguments(arguments, endpoint)
    logger.debug("Normalized arguments keys: %s", list(normalized_args.keys()))

    initial_values = {'inputs': {}, 'parameters': {}}
    path_types = {InputType.DIRECTORY, InputType.FILE}

    for input_schema in task_schema.inputs:
        if (key := input_schema.key) in normalized_args:
            wrapper = 'path' if input_schema.input_type in path_types else 'text'
            initial_values['inputs'][key] = {wrapper: str(normalized_args[key])}

    for param_schema in task_schema.parameters:
        if (key := param_schema.key) in normalized_args:
            initial_values['parameters'][key] = normalized_args[key]

    logger.info("Conversion complete: %d inputs, %d parameters",
               len(initial_values['inputs']), len(initial_values['parameters']))
    return initial_values

