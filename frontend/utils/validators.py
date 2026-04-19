"""
Form Validation Utilities

Validates **inputs** with Pydantic. An optional recursive raster scan applies
only to ``input_dir`` when key/label/subtitle suggest an image corpus (and not
audio); output directory keys and paired sinks are excluded. Text/textarea
inputs whose schema key is ``query`` (e.g. image/text search) must be non-empty
after strip. **Parameters** submitted to :func:`validate_form_data` are not
checked against ``TaskSchema`` (pass-through). Use :func:`validate_parameter`
for standalone descriptor checks.
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


def _required_query_user_message(input_schema: InputSchema) -> str:
    label = (input_schema.label or "").strip() or "Search query"
    return f"{label} is required. Enter what to search for before submitting."


def _input_schema_is_text_or_textarea(input_schema: InputSchema) -> bool:
    it = input_schema.input_type
    if isinstance(it, InputType):
        return it in (InputType.TEXT, InputType.TEXTAREA)
    if isinstance(it, str):
        return it.lower() in ("text", "textarea")
    return False


def _strip_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _is_empty_input_value(input_schema: InputSchema, value: Any) -> bool:
    """
    True when the user left a path/file (or batch thereof) unset.

    Other text/textarea fields may be empty. The ``query`` text input must be
    non-empty (strip) for search-style forms.
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

    # Search plugins (e.g. image_embeddings/search_images) use input key ``query`` for the phrase.
    if _input_schema_is_text_or_textarea(input_schema) and (
        (input_schema.key or "").strip().lower() == "query"
    ):
        if value is None:
            return True
        if isinstance(value, dict):
            return not _strip_str(value.get("text"))
        return not _strip_str(value)

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

def _input_schema_is_directory_or_batch_directory(input_schema: InputSchema) -> bool:
    it = input_schema.input_type
    if isinstance(it, InputType):
        return it in (InputType.DIRECTORY, InputType.BATCHDIRECTORY)
    if isinstance(it, str):
        return it.lower() in ("directory", "batchdirectory")
    return False


# Directory inputs that hold plugin output — must not require raster images (often empty).
_OUTPUT_DIRECTORY_INPUT_KEYS = frozenset(
    {
        "output_dir",
        "output_directory",
        "out_dir",
        "output_folder",
        "destination_dir",
    }
)


def _input_schema_is_output_destination_directory(
    input_schema: InputSchema,
    *,
    all_inputs: Optional[List[Any]] = None,
    input_index: Optional[int] = None,
) -> bool:
    """True when this field is an output/sink folder, not a folder of source images."""
    key = (input_schema.key or "").strip().lower()
    if key in _OUTPUT_DIRECTORY_INPUT_KEYS:
        return True
    if all_inputs is not None and input_index is not None and input_index > 0:
        try:
            from frontend.utils.job_form_paths import paired_output_directory_field_id
        except ImportError:
            return False
        paired = paired_output_directory_field_id(list(all_inputs), input_index - 1)
        if paired and paired == input_schema.key:
            return True
    return False


def _input_schema_directory_requires_raster_image_corpus(
    input_schema: InputSchema,
    *,
    all_inputs: Optional[List[Any]] = None,
    input_index: Optional[int] = None,
) -> bool:
    """
    True only for ``input_dir`` when labels look image-related (not audio).

    Other directory keys are never scanned. Generic ``input files`` style labels
    (no ``image`` / ``photo`` / ``picture`` substring) skip the scan.
    """
    if not _input_schema_is_directory_or_batch_directory(input_schema):
        return False
    if _input_schema_is_output_destination_directory(
        input_schema, all_inputs=all_inputs, input_index=input_index
    ):
        return False
    if (input_schema.key or "").strip().lower() != "input_dir":
        return False
    blob = (
        f"{input_schema.key} {(input_schema.label or '')} "
        f"{(getattr(input_schema, 'subtitle', None) or '')}"
    ).lower()
    if "audio" in blob:
        return False
    if not any(w in blob for w in ("image", "photo", "picture")):
        return False
    return True


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
    Validate form **inputs** against a TaskSchema using Pydantic models.

    Converts values to ``FileInput``, ``DirectoryInput``, etc. Applies a bounded
    raster scan only for ``input_dir`` when the field text suggests images (see
    :func:`_input_schema_directory_requires_raster_image_corpus`). **Parameters**
    are copied from the form unchanged (no descriptor validation here).
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
        
        inputs_list = list(task_schema.inputs)
        for input_index, input_schema in enumerate(inputs_list):
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
                if _input_schema_is_text_or_textarea(input_schema) and (
                    (input_schema.key or "").strip().lower() == "query"
                ):
                    errors[field_id] = _required_query_user_message(input_schema)
                else:
                    errors[field_id] = _required_input_user_message(input_schema)
                continue
            if pipeline_only and _is_empty_input_value(input_schema, field_value):
                logger.debug("Pipeline-only input '%s' empty; skipping validation", field_id)
                continue

            logger.debug("Validating input field: %s", field_id)
            
            try:
                # Create appropriate Input model based on input_type
                input_model = _create_input_model(input_schema, field_value)
                if _input_schema_directory_requires_raster_image_corpus(
                    input_schema,
                    all_inputs=inputs_list,
                    input_index=input_index,
                ):
                    label = (input_schema.label or "").strip() or field_id
                    _raster_msg = (
                        f"this folder has no common image files "
                        f"({', '.join(s.strip('.') for s in _COMMON_RASTER_IMAGE_SUFFIXES[:6])}, …). "
                        "Add images or choose another folder."
                    )
                    if isinstance(input_model, DirectoryInput):
                        if not _directory_contains_raster_image(input_model.path):
                            errors[field_id] = f"{label}: {_raster_msg}"
                            continue
                    elif isinstance(input_model, BatchDirectoryInput):
                        for j, d in enumerate(input_model.directories):
                            if not _directory_contains_raster_image(d.path):
                                errors[field_id] = (
                                    f"{label} (folder {j + 1}): {_raster_msg}"
                                )
                                break
                        else:
                            pass
                        if field_id in errors:
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
        
        logger.debug("Collecting parameters (pass-through; no TaskSchema checks)")
        parameters_dict = dict(form_data.get("parameters", {}))

        # Build RequestBody if no errors so far
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
    """Used by :func:`validate_parameter` only; not called from :func:`validate_form_data`."""
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
            labels_str = ", ".join(
                [enum_val.label or enum_val.key for enum_val in param_descriptor.enum_vals]
            )
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
        endpoint (Optional[str]): Passed through to :func:`validate_form_data` (optional for callers).
    
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
    Validate a parameter value against its descriptor (standalone helper).

    :func:`validate_form_data` does not use this; parameters are pass-through there.
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