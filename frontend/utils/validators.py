"""
Form Validation Utilities

This module provides validation functions for form data using Pydantic models
from the RescueBox API. It validates inputs and parameters against TaskSchema
definitions and converts form data to RequestBody format.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from pydantic import ValidationError
import sys
from pathlib import Path

# Add backend models to path (adjust import path as needed)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from rb.api.models import (
    TaskSchema,
    InputSchema,
    ParameterSchema,
    RequestBody,
    Input,
    FileInput,
    DirectoryInput,
    TextInput,
    BatchFileInput,
    BatchTextInput,
    BatchDirectoryInput,
    InputType,
    NewFileInputType,
    ParameterType,
    RangedFloatParameterDescriptor,
    RangedIntParameterDescriptor,
    FloatParameterDescriptor,
    IntParameterDescriptor,
    EnumParameterDescriptor,
    TextParameterDescriptor,
    FileResponse,
    DirectoryResponse,
    MarkdownResponse,
    TextResponse,
    BatchFileResponse,
    BatchTextResponse,
    BatchDirectoryResponse,
    ResponseBody,
)


def _required_input_user_message(input_schema: InputSchema) -> str:
    label = (input_schema.label or "").strip() or input_schema.key
    return (
        f"{label} is required. Choose a folder or file with Browse, "
        "or enter a valid path, before submitting."
    )


def _strip_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _is_empty_input_value(input_schema: InputSchema, value: Any) -> bool:
    """
    True when the user left a path/file (or batch thereof) unset.

    Text and textarea fields may be empty unless Pydantic rejects them later.
    """
    it = input_schema.input_type
    if isinstance(it, InputType):
        type_key = it.value
    elif isinstance(it, str):
        type_key = it.lower()
    elif isinstance(it, NewFileInputType):
        type_key = "newfile"
    else:
        type_key = str(it).lower()

    if type_key in ("file", "directory", "newfile"):
        if value is None:
            return True
        if isinstance(value, dict):
            return not _strip_str(value.get("path"))
        return not _strip_str(value)

    if type_key == "batchfile":
        if value is None:
            return True
        files: List[Any]
        if isinstance(value, dict) and isinstance(value.get("files"), list):
            files = value["files"]
        elif isinstance(value, list):
            files = value
        else:
            return True
        if not files:
            return True
        for item in files:
            if isinstance(item, dict):
                if not _strip_str(item.get("path")):
                    return True
            elif not _strip_str(item):
                return True
        return False

    if type_key == "batchdirectory":
        if value is None:
            return True
        items: List[Any]
        if isinstance(value, dict) and isinstance(value.get("directories"), list):
            items = value["directories"]
        elif isinstance(value, list):
            items = value
        else:
            return True
        if not items:
            return True
        for item in items:
            if isinstance(item, dict):
                if not _strip_str(item.get("path")):
                    return True
            elif not _strip_str(item):
                return True
        return False

    if type_key == "batchtext":
        if value is None:
            return True
        texts = value if isinstance(value, list) else []
        if not texts:
            return True
        for item in texts:
            if isinstance(item, dict):
                if _strip_str(item.get("text")):
                    return False
            elif _strip_str(item):
                return False
        return True

    return False


# Raster extensions commonly produced by cameras / evidence workflows (case-insensitive match on suffix)
_COMMON_RASTER_IMAGE_SUFFIXES: tuple[str, ...] = (
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

# Endpoints whose primary ``directory`` inputs must contain at least one raster image file.
_IMAGE_DIRECTORY_ENDPOINT_MARKERS: tuple[str, ...] = (
    "image_summary",
    "summarize-images",
    "image_embedding",
    "image-embedding",
    "search_images",
    "search-images",
    "describe-images",
    "describe_images",
    "face_detection",
    "face-detection",
    "face_recognition",
    "face-recognition",
    "find_face",
    "find-face",
    "age_gender",
    "age-gender",
    "age_and_gender",
    "deepfake",
    "image_bbox",
    "object_detect",
    "object-detect",
)

# If ``endpoint`` is unknown, use label/subtitle/key heuristics, but avoid obvious non-image tasks.
_IMAGE_DIRECTORY_HINT_POSITIVE: tuple[str, ...] = (
    "image",
    "photo",
    "picture",
    "jpeg",
    "png",
    "webp",
    "thumbnail",
    "caption",
    "visual",
    "album",
    "face",
    "clip",
)
_IMAGE_DIRECTORY_HINT_NEGATIVE: tuple[str, ...] = (
    "audio",
    "transcript",
    "speech",
    "wav",
    "mp3",
    "flac",
    "text file",
    "folder of .txt",
    ".txt files",
    "plain text",
)


def _normalize_endpoint_for_matching(endpoint: Optional[str]) -> str:
    if not endpoint:
        return ""
    return endpoint.lower().replace("_", "-").strip("/ ")


def _endpoint_expects_raster_image_directory(endpoint: Optional[str]) -> bool:
    el = _normalize_endpoint_for_matching(endpoint)
    if not el:
        return False
    if "text_embedding" in el or "text-embedding" in el:
        return False
    return any(marker in el for marker in _IMAGE_DIRECTORY_ENDPOINT_MARKERS)


def _input_schema_hints_raster_image_directory(input_schema: InputSchema) -> bool:
    blob = (
        f"{input_schema.key} {(input_schema.label or '')} "
        f"{(getattr(input_schema, 'subtitle', None) or '')}"
    ).lower()
    if any(s in blob for s in _IMAGE_DIRECTORY_HINT_NEGATIVE):
        return False
    return any(s in blob for s in _IMAGE_DIRECTORY_HINT_POSITIVE)


def _input_schema_is_directory_type(input_schema: InputSchema) -> bool:
    it = input_schema.input_type
    if isinstance(it, InputType):
        return it == InputType.DIRECTORY
    if isinstance(it, str):
        return it.lower() == "directory"
    return False


def _should_check_directory_contains_raster_images(
    input_schema: InputSchema,
    endpoint: Optional[str],
) -> bool:
    if not _input_schema_is_directory_type(input_schema):
        return False
    if _endpoint_expects_raster_image_directory(endpoint):
        return True
    if not endpoint and _input_schema_hints_raster_image_directory(input_schema):
        return True
    return False


def _directory_contains_raster_image(root: Path, *, max_files_scanned: int = 12000) -> bool:
    """
    Return True if ``root`` (recursively) contains at least one file whose suffix
    matches common raster image types. Bounded scan for large trees.
    """
    try:
        resolved = root.expanduser()
        try:
            resolved = resolved.resolve(strict=False)
        except OSError:
            return False
    except OSError:
        return False
    if not resolved.is_dir():
        return False
    scanned = 0
    try:
        for p in resolved.rglob("*"):
            if not p.is_file():
                continue
            if p.name.startswith("."):
                continue
            scanned += 1
            if scanned > max_files_scanned:
                return False
            low = p.name.lower()
            if any(low.endswith(suf) for suf in _COMMON_RASTER_IMAGE_SUFFIXES):
                return True
    except OSError:
        return False
    return False


def validate_form_data(
    form_data: Dict,
    schema: Union[TaskSchema, Dict],
    endpoint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate form data against TaskSchema using Pydantic models.
    
    This function validates form input data against a TaskSchema, converting
    form values to appropriate Pydantic models (FileInput, DirectoryInput, etc.)
    and validating parameters according to their descriptors.
    
    The validation process:
    1. Converts schema dict to TaskSchema if needed
    2. Validates each input field and creates appropriate Input models
    3. Validates each parameter against its descriptor
    4. Creates RequestBody model if all validations pass
    
    Args:
        form_data (Dict): Form data dictionary with structure:
            {
                'inputs': {key: {'path': value} or {'text': value}, ...},
                'parameters': {key: value, ...}
            }
        schema (Union[TaskSchema, Dict]): TaskSchema Pydantic model or dictionary.
            If dict, it will be converted to TaskSchema
        endpoint (Optional[str]): Task route (e.g. ``image_summary/summarize-images``). When it
            matches image-style plugins, ``directory`` inputs must contain at least one common
            raster image file under the chosen folder (recursive scan, bounded).
    
    Returns:
        Dict[str, Any]: Validation result dictionary with:
            - 'is_valid' (bool): True if validation passed
            - 'errors' (Dict): Dictionary of field errors (if validation failed)
            - 'validated_data' (RequestBody, optional): Validated RequestBody model (if valid)
    
    Examples:
        >>> result = validate_form_data(
        ...     {'inputs': {'input_dir': {'path': '/tmp'}}, 'parameters': {}},
        ...     task_schema
        ... )
        >>> if result['is_valid']:
        ...     request_body = result['validated_data']
    
    Tips:
    - Every normal (non-pipeline-only) input in the task schema must be present; path/file/batch
      values must be non-empty. Inputs with ``exclude_from_client_schema`` (e.g. ``file_filter``)
      are optional when absent; when present they are validated.
    - Each present field is validated with Pydantic Input models (paths must exist where applicable).
    - Validation errors are formatted for user display
    - Returns RequestBody model on success for direct API submission
    """
    logger.info("Validating form data against TaskSchema")
    logger.debug("Form data keys: inputs=%d, parameters=%d", len(form_data.get('inputs', {})), len(form_data.get('parameters', {})))
    
    errors = {}
    
    # Convert schema to Pydantic model if it's a dict
    if isinstance(schema, dict):
        logger.debug("Converting dictionary schema to TaskSchema")
        try:
            task_schema = TaskSchema(**schema)
        except ValidationError as e:
            logger.error("Schema validation failed")
            return {
                'is_valid': False,
                'errors': {'schema': _format_validation_error(e)}
            }
    else:
        task_schema = schema
    
    # Build RequestBody and validate
    try:
        logger.debug("Validating input fields")
        # Convert inputs to Pydantic Input models
        inputs_dict = {}
        inputs_data = form_data.get('inputs', {})
        
        for input_schema in task_schema.inputs:
            field_id = input_schema.key
            pipeline_only = getattr(input_schema, "exclude_from_client_schema", False)

            if field_id not in inputs_data:
                if pipeline_only:
                    logger.debug("Pipeline-only input '%s' absent; skipping", field_id)
                    continue
                logger.warning("Input field '%s' missing from submitted form data", field_id)
                errors[field_id] = _required_input_user_message(input_schema)
                continue

            field_value = inputs_data[field_id]
            if not pipeline_only and _is_empty_input_value(input_schema, field_value):
                logger.warning("Input field '%s' is empty", field_id)
                errors[field_id] = _required_input_user_message(input_schema)
                continue
            if pipeline_only and _is_empty_input_value(input_schema, field_value):
                logger.debug("Pipeline-only input '%s' empty; skipping validation", field_id)
                continue

            logger.debug("Validating input field: %s", field_id)
            
            try:
                # Create appropriate Input model based on input_type
                input_model = _create_input_model(input_schema, field_value)
                if _should_check_directory_contains_raster_images(input_schema, endpoint):
                    if isinstance(input_model, DirectoryInput) and not _directory_contains_raster_image(
                        input_model.path
                    ):
                        label = (input_schema.label or "").strip() or field_id
                        errors[field_id] = (
                            f"{label}: this folder has no common image files "
                            f"({', '.join(s.strip('.') for s in _COMMON_RASTER_IMAGE_SUFFIXES[:6])}, …). "
                            "Add images or choose another folder."
                        )
                        continue
                inputs_dict[field_id] = Input(root=input_model)
                logger.debug("Input field '%s' validated successfully", field_id)
            except ValidationError as e:
                logger.warning("Input field '%s' validation failed: %s", field_id, _format_validation_error(e))
                errors[field_id] = _format_validation_error(e)
            except Exception as e:
                logger.error("Input field '%s' validation error: %s", field_id, str(e))
                errors[field_id] = str(e)

        # Inputs present in POST but omitted from public GET task_schema (e.g. file_filter).
        schema_keys = {input_schema.key for input_schema in task_schema.inputs}
        for extra_key, extra_val in inputs_data.items():
            if extra_key in schema_keys or extra_key in inputs_dict:
                continue
            if extra_key != "file_filter":
                continue
            try:
                ff_schema = InputSchema(
                    key="file_filter",
                    label="File filter",
                    input_type=InputType.BATCHFILE,
                )
                input_model = _create_input_model(ff_schema, extra_val)
                inputs_dict[extra_key] = Input(root=input_model)
                logger.debug("Validated pipeline-only input '%s'", extra_key)
            except ValidationError as e:
                logger.warning("Pipeline input '%s' validation failed: %s", extra_key, _format_validation_error(e))
                errors[extra_key] = _format_validation_error(e)
            except Exception as e:
                logger.error("Pipeline input '%s' error: %s", extra_key, str(e))
                errors[extra_key] = str(e)
        
        logger.debug("Validating parameters")
        # Validate parameters (they're Dict[str, Any] in RequestBody)
        parameters_dict = {}
        parameters_data = form_data.get('parameters', {})
        
        for param_schema in task_schema.parameters:
            param_id = param_schema.key
            if param_id not in parameters_data:
                logger.debug("Parameter '%s' not in form data, skipping", param_id)
                continue
            
            param_value = parameters_data[param_id]
            logger.debug("Validating parameter: %s", param_id)
            
            try:
                # Validate parameter against its descriptor
                _validate_parameter_value(param_value, param_schema)
                parameters_dict[param_id] = param_value
                logger.debug("Parameter '%s' validated successfully", param_id)
            except ValidationError as e:
                logger.warning("Parameter '%s' validation failed: %s", param_id, _format_validation_error(e))
                errors[param_id] = _format_validation_error(e)
            except Exception as e:
                logger.error("Parameter '%s' validation error: %s", param_id, str(e))
                errors[param_id] = str(e)
        
        # Validate entire RequestBody if no errors so far
        if not errors:
            logger.debug("All validations passed, creating RequestBody")
            request_body = RequestBody(
                inputs=inputs_dict,
                parameters=parameters_dict
            )
            # If we get here, validation passed
            logger.info("Form validation successful: %d inputs, %d parameters", len(inputs_dict), len(parameters_dict))
            return {
                'is_valid': True,
                'errors': {},
                'validated_data': request_body
            }
    
    except ValidationError as e:
        # Catch any remaining validation errors
        logger.error("RequestBody validation error: %s", _format_validation_error(e))
        return {
            'is_valid': False,
            'errors': {'request_body': _format_validation_error(e)}
        }
    except Exception as e:
        logger.error("Unexpected validation error: %s", str(e))
        return {
            'is_valid': False,
            'errors': {'general': str(e)}
        }
    
    logger.warning("Form validation failed with %d errors", len(errors))
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }

def _create_input_model(input_schema: InputSchema, value: Any) -> Union[
    FileInput, DirectoryInput, TextInput, BatchFileInput, BatchTextInput, BatchDirectoryInput
]:
    """
    Create appropriate Input model from schema and value.
    
    This helper function creates the correct Pydantic Input model based on
    the input type specified in the schema. It handles both dict and primitive
    value formats.
    
    Args:
        input_schema (InputSchema): Schema defining the input field
        value (Any): Input value, either a dict (e.g., {'path': '/tmp'}) or primitive
    
    Returns:
        Union[FileInput, DirectoryInput, TextInput, BatchFileInput, BatchTextInput, BatchDirectoryInput]:
            Appropriate Input model instance
    
    Raises:
        ValidationError: If value format is invalid for the input type
        ValueError: If input type is not recognized
    
    Tips:
    - FILE/DIRECTORY expect {'path': value} or string path
    - TEXT/TEXTAREA expect {'text': value} or string text
    - BATCH types expect lists of file/directory/text items
    """
    logger.debug("Creating input model for type: %s", input_schema.input_type)
    input_type = input_schema.input_type
    
    # Handle InputType enum
    if isinstance(input_type, InputType):
        if input_type == InputType.FILE:
            path = value.get('path') if isinstance(value, dict) else str(value)
            return FileInput(path=Path(path))
        
        elif input_type == InputType.DIRECTORY:
            path = value.get('path') if isinstance(value, dict) else str(value)
            return DirectoryInput(path=Path(path))
        
        elif input_type == InputType.TEXT or input_type == InputType.TEXTAREA:
            text = value.get('text') if isinstance(value, dict) else str(value)
            return TextInput(text=text)
        
        elif input_type == InputType.BATCHFILE:
            if isinstance(value, dict) and "files" in value:
                files_data = value.get("files") or []
            elif isinstance(value, list):
                files_data = value
            else:
                files_data = []
            files = [
                FileInput(path=Path(f.get("path") if isinstance(f, dict) else f))
                for f in files_data
            ]
            return BatchFileInput(files=files)
        
        elif input_type == InputType.BATCHTEXT:
            texts_data = value if isinstance(value, list) else []
            texts = [TextInput(text=t.get('text') if isinstance(t, dict) else str(t)) for t in texts_data]
            return BatchTextInput(texts=texts)
        
        elif input_type == InputType.BATCHDIRECTORY:
            dirs_data = value if isinstance(value, list) else []
            directories = [DirectoryInput(path=Path(d.get('path') if isinstance(d, dict) else d)) for d in dirs_data]
            return BatchDirectoryInput(directories=directories)
    
    # If we get here, raise error
    raise ValueError(f"Unsupported input type: {input_type}")

def _validate_parameter_value(value: Any, param_schema: ParameterSchema) -> None:
    """
    Validate parameter value against parameter schema descriptor.
    
    This helper function validates a parameter value according to its descriptor
    type (ranged, enum, text, etc.) and checks constraints like min/max, enum values.
    
    Args:
        value (Any): Parameter value to validate
        param_schema (ParameterSchema): Schema with parameter descriptor
    
    Raises:
        ValidationError: If value fails validation (out of range, invalid enum, etc.)
        ValueError: If parameter descriptor type is not recognized
    
    Tips:
    - Ranged parameters check min/max boundaries
    - Enum parameters check against allowed values
    - Type validation is performed automatically by Pydantic
    """
    logger.debug("Validating parameter value for '%s'", param_schema.key)
    param_descriptor = param_schema.value
    
    if isinstance(param_descriptor, RangedFloatParameterDescriptor):
        if not isinstance(value, (int, float)):
            raise ValueError(f"Expected float, got {type(value).__name__}")
        if value < param_descriptor.range.min or value > param_descriptor.range.max:
            raise ValueError(
                f"Value {value} must be between {param_descriptor.range.min} and {param_descriptor.range.max}"
            )
    
    elif isinstance(param_descriptor, RangedIntParameterDescriptor):
        if not isinstance(value, (int, float)):
            raise ValueError(f"Expected int, got {type(value).__name__}")
        int_value = int(value)
        if int_value < param_descriptor.range.min or int_value > param_descriptor.range.max:
            raise ValueError(
                f"Value {int_value} must be between {param_descriptor.range.min} and {param_descriptor.range.max}"
            )
    
    elif isinstance(param_descriptor, FloatParameterDescriptor):
        if not isinstance(value, (int, float)):
            raise ValueError(f"Expected float, got {type(value).__name__}")
    
    elif isinstance(param_descriptor, IntParameterDescriptor):
        if not isinstance(value, (int, float)):
            raise ValueError(f"Expected int, got {type(value).__name__}")
    
    elif isinstance(param_descriptor, EnumParameterDescriptor):
        if not param_descriptor.enum_vals:
            logger.warning(
                "Parameter '%s' has an empty enum in the task schema; skipping membership check",
                param_schema.key,
            )
            return
        valid_keys = [enum_val.key for enum_val in param_descriptor.enum_vals if enum_val.key]
        valid_labels = [enum_val.label for enum_val in param_descriptor.enum_vals if enum_val.label]
        if value not in valid_keys and value not in valid_labels:
            labels_str = ', '.join([enum_val.label or enum_val.key for enum_val in param_descriptor.enum_vals])
            raise ValueError(f"Value must be one of: {labels_str}")
    
    elif isinstance(param_descriptor, TextParameterDescriptor):
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value).__name__}")

def _format_validation_error(e: ValidationError) -> str:
    """
    Format Pydantic ValidationError into user-friendly error message.
    
    Extracts and formats validation errors from Pydantic's ValidationError
    exception for display to users.
    
    Args:
        e (ValidationError): Pydantic ValidationError exception
    
    Returns:
        str: Formatted error message string
    
    Tips:
    - Extracts first error message for simplicity
    - Combines field location and error message
    - Returns readable error text for UI display
    """
    errors = []
    for error in e.errors():
        field = ' -> '.join(str(loc) for loc in error['loc'])
        msg = error['msg']
        errors.append(f"{field}: {msg}")
    
    formatted = '; '.join(errors) if errors else str(e)
    logger.debug("Formatted validation error: %s", formatted)
    return formatted

def validate_request_body(
    data: Dict,
    task_schema: Union[TaskSchema, Dict],
    endpoint: Optional[str] = None,
) -> Union[RequestBody, Dict[str, Any]]:
    """
    Validate and create RequestBody from form data.
    
    Convenience wrapper around validate_form_data that returns the RequestBody
    directly if valid, or error dictionary if invalid.
    
    Args:
        data (Dict): Form data dictionary
        task_schema (Union[TaskSchema, Dict]): TaskSchema model or dict
        endpoint (Optional[str]): Passed through to :func:`validate_form_data` for task-kind checks.
    
    Returns:
        Union[RequestBody, Dict[str, Any]]: Validated RequestBody if valid,
            or dict with 'is_valid': False and 'errors' if invalid
    
    Examples:
        >>> request_body = validate_request_body(form_data, task_schema, endpoint=endpoint)
        >>> if isinstance(request_body, RequestBody):
        ...     # Submit to API
        ...     pass
    
    Tips:
    - Returns RequestBody directly on success (no need to extract from dict)
    - Returns error dict on failure (same format as validate_form_data)
    """
    logger.debug("Validating request body")
    result = validate_form_data(data, task_schema, endpoint=endpoint)
    
    if result['is_valid']:
        logger.info("RequestBody validation successful")
        return result.get('validated_data')
    else:
        logger.warning("RequestBody validation failed")
        return result

def validate_response_body(data: Dict) -> Union[ResponseBody, Dict[str, Any]]:
    """
    Validate response data against ResponseBody model.
    
    Validates API response data by attempting to create a ResponseBody Pydantic
    model. Returns the model if valid, or error dictionary if invalid.
    
    Args:
        data (Dict): Response data dictionary from API
    
    Returns:
        Union[ResponseBody, Dict[str, Any]]: Validated ResponseBody if valid,
            or dict with 'is_valid': False and 'errors' if invalid
    
    Examples:
        >>> response = validate_response_body(api_response_data)
        >>> if isinstance(response, ResponseBody):
        ...     # Process valid response
        ...     pass
    
    Tips:
    - Use this to validate API responses before processing
    - Returns ResponseBody directly on success
    - Returns error dict with validation details on failure
    """
    logger.debug("Validating response body")
    try:
        response_body = ResponseBody(**data)
        logger.info("ResponseBody validation successful")
        return response_body
    except ValidationError as e:
        # Try legacy/flat response shapes and wrap into ResponseBody.root where possible
        logger.debug("ResponseBody validation failed, attempting legacy shape conversion: %s", _format_validation_error(e))
        try:
            ot = data.get('output_type')
            if ot == 'file':
                fr = FileResponse(**{
                    'file_type': data.get('file_type'),
                    'path': data.get('path'),
                    'title': data.get('title'),
                    'subtitle': data.get('subtitle'),
                    'metadata': data.get('metadata')
                })
                return ResponseBody(root=fr)
            if ot == 'text':
                tr = TextResponse(**{
                    'value': data.get('value'),
                    'title': data.get('title'),
                    'subtitle': data.get('subtitle')
                })
                return ResponseBody(root=tr)
            if ot == 'markdown':
                mr = MarkdownResponse(**{
                    'value': data.get('value'),
                    'title': data.get('title'),
                    'subtitle': data.get('subtitle')
                })
                return ResponseBody(root=mr)
            if ot == 'directory':
                dr = DirectoryResponse(**{
                    'path': data.get('path'),
                    'title': data.get('title'),
                    'subtitle': data.get('subtitle')
                })
                return ResponseBody(root=dr)
            if ot == 'batchfile' and 'files' in data:
                files = [FileResponse(**f) for f in data.get('files', [])]
                bfr = BatchFileResponse(files=files)
                return ResponseBody(root=bfr)
        except Exception:
            logger.debug("Legacy shape conversion failed or not applicable")
        logger.warning("ResponseBody validation failed: %s", _format_validation_error(e))
        return {
            'is_valid': False,
            'errors': {'response': _format_validation_error(e)}
        }

# Backward compatibility functions (deprecated, use validate_form_data instead)
def validate_input(value: Any, input_schema: Union[InputSchema, Dict]) -> Optional[str]:
    """
    Validate an input field value (deprecated, use validate_form_data)
    
    This is kept for backward compatibility but delegates to Pydantic validation
    """
    if isinstance(input_schema, dict):
        try:
            input_schema = InputSchema(**input_schema)
        except ValidationError:
            return "Invalid input schema"
    
    try:
        _create_input_model(input_schema, value)
        return None
    except ValidationError as e:
        return _format_validation_error(e)
    except Exception as e:
        return str(e)

def validate_parameter(value: Any, param_schema: Union[ParameterSchema, Dict]) -> Optional[str]:
    """
    Validate a parameter value (deprecated, use validate_form_data)
    
    This is kept for backward compatibility but delegates to Pydantic validation
    """
    if isinstance(param_schema, dict):
        try:
            param_schema = ParameterSchema(**param_schema)
        except ValidationError:
            return "Invalid parameter schema"
    
    try:
        _validate_parameter_value(value, param_schema)
        return None
    except (ValidationError, ValueError) as e:
        return str(e)