import logging
from typing import Dict, List, Optional, Any, Union
from pydantic import ValidationError
from rb.api.models import (
    DirectoryInput, FileInput, InputType, TaskSchema, Input, 
    RequestBody, InputSchema, TextInput, ResponseBody
)
from .paths import (
    _resolve_input_path, _input_schema_directory_requires_raster_image_corpus,
    _directory_contains_raster_image
)

logger = logging.getLogger(__name__)

_OUTPUT_DIRECTORY_INPUT_KEYS = frozenset({"output_dir", "output_directory", "out_dir", "output_folder", "destination_dir"})

def _required_input_user_message(input_schema: InputSchema) -> str:
    label = (input_schema.label or "").strip() or input_schema.key
    return f"{label} is required. Choose a folder or file with Browse, or enter a valid path, before submitting."

def _required_query_user_message(input_schema: InputSchema) -> str:
    label = (input_schema.label or "").strip() or "Search query"
    return f"{label} is required. Enter what to search for before submitting."

def _input_schema_is_text_or_textarea(input_schema: InputSchema) -> bool:
    it = input_schema.input_type
    return it in (InputType.TEXT, InputType.TEXTAREA)

def _coerce_input_type(schema: Any) -> Optional[Any]:
    from rb.api.models import InputType
    it = getattr(schema, "input_type", None)
    if it is None: return None
    if isinstance(it, InputType): return it
    try: return InputType(it)
    except: return None

def paired_output_directory_field_id(inputs_list: List[Any], index: int) -> Optional[str]:
    from rb.api.models import InputType
    if not inputs_list or index < 0 or index >= len(inputs_list): return None
    cur = inputs_list[index]
    if _coerce_input_type(cur) != InputType.DIRECTORY: return None
    key = getattr(cur, "key", None)
    if key not in ("input_dir", "input_dataset"): return None
    if index + 1 >= len(inputs_list): return None
    nxt = inputs_list[index + 1]
    if _coerce_input_type(nxt) != InputType.DIRECTORY: return None
    nxt_key = getattr(nxt, "key", None)
    if nxt_key not in ("output_dir", "output_file"): return None
    return nxt_key

def paired_ufdr_mount_name_field_id(inputs_list: List[Any], index: int) -> Optional[str]:
    from rb.api.models import InputType
    if not inputs_list or index < 0 or index >= len(inputs_list): return None
    cur = inputs_list[index]
    if getattr(cur, "key", None) != "ufdr_file": return None
    if _coerce_input_type(cur) != InputType.FILE: return None
    if index + 1 >= len(inputs_list): return None
    nxt = inputs_list[index + 1]
    if getattr(nxt, "key", None) != "mount_name": return None
    if _coerce_input_type(nxt) != InputType.TEXT: return None
    return "mount_name"

def validate_form_data(
    form_data: Dict,
    schema: Union[TaskSchema, Dict],
    endpoint: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate form inputs against a TaskSchema using Pydantic models."""
    errors = {}
    try:
        task_schema = TaskSchema(**schema) if isinstance(schema, dict) else schema
    except (ValidationError, TypeError, ValueError) as e:
        return {'is_valid': False, 'errors': {'schema': str(e)}}
    
    inputs_dict = {}
    inputs_data = form_data.get('inputs', {})
    
    inputs_list = list(task_schema.inputs)
    for input_index, input_schema in enumerate(inputs_list):
        field_id = input_schema.key
        if field_id not in inputs_data:
            errors[field_id] = _required_input_user_message(input_schema)
            continue

        field_value = inputs_data[field_id]
        if _is_empty_input_value(input_schema, field_value):
            if _input_schema_is_text_or_textarea(input_schema) and (input_schema.key or "").strip().lower() == "query":
                errors[field_id] = _required_query_user_message(input_schema)
            else:
                errors[field_id] = _required_input_user_message(input_schema)
            continue

        try:
            input_model = _create_input_model(input_schema, field_value)
            if _input_schema_directory_requires_raster_image_corpus(
                input_schema,
                all_inputs=inputs_list,
                input_index=input_index,
            ):
                if isinstance(input_model, DirectoryInput):
                    if not _directory_contains_raster_image(input_model.path):
                        errors[field_id] = f"{input_schema.label or field_id}: folder has no common image files."
                        continue
            inputs_dict[field_id] = Input(root=input_model)
        except ValidationError as e:
            errors[field_id] = str(e)
        except Exception as e:
            errors[field_id] = str(e)
            
    if errors:
        return {'is_valid': False, 'errors': errors}
    
    return {
        'is_valid': True,
        'errors': {},
        'validated_data': RequestBody(
            inputs=inputs_dict,
            parameters=dict(form_data.get("parameters", {}))
        )
    }

def _create_input_model(input_schema, value):
    it = input_schema.input_type
    if it == InputType.FILE: return FileInput(path=_resolve_input_path(value))
    if it == InputType.DIRECTORY: return DirectoryInput(path=_resolve_input_path(value))
    if it in (InputType.TEXT, InputType.TEXTAREA):
        text = value.get('text') if isinstance(value, dict) else str(value)
        return TextInput(text=text)
    raise ValueError(f"Unsupported type: {it}")

def validate_response_body(data: Dict) -> Union[ResponseBody, Dict[str, Any]]:
    try: return ResponseBody(**data)
    except ValidationError as e:
        return {'is_valid': False, 'errors': {'response': str(e)}}

def validate_request_body(data: Dict, task_schema: Optional[TaskSchema] = None, endpoint: str = "") -> Union[RequestBody, Dict[str, Any]]:
    """Validate a request body dictionary against the RequestBody model."""
    try: return RequestBody(**data)
    except ValidationError as e:
        return {'is_valid': False, 'errors': {'request': str(e)}}

def _is_empty_input_value(input_schema: InputSchema, value: Any) -> bool:
    it = input_schema.input_type
    if it in (InputType.FILE, InputType.DIRECTORY):
        p = value.get('path') if isinstance(value, dict) else value
        return not str(p or "").strip()
    if it in (InputType.TEXT, InputType.TEXTAREA):
        if (input_schema.key or "").strip().lower() == "query":
            t = value.get('text') if isinstance(value, dict) else value
            return not str(t or "").strip()
    return False

def _validate_parameter_value(value: Any, param_schema: Any) -> None:
    """Validate a single parameter value against its schema."""
    if value is None: return
    from rb.api.models import RangedFloatParameterDescriptor, EnumParameterDescriptor
    desc = param_schema.value
    if isinstance(desc, RangedFloatParameterDescriptor):
        if not (desc.range.min <= float(value) <= desc.range.max):
            raise ValueError(f"Value {value} must be between {desc.range.min} and {desc.range.max}")
    elif isinstance(desc, EnumParameterDescriptor):
        valid_values = [v.key for v in desc.enum_vals]
        if value not in valid_values:
            raise ValueError(f"Value must be one of: {', '.join(valid_values)}")

def _format_validation_error(e: ValidationError) -> str:
    """Format a Pydantic ValidationError into a user-friendly string."""
    errors = e.errors()
    if not errors: return str(e)
    messages = []
    for err in errors:
        loc = " -> ".join(str(item) for item in err['loc'])
        msg = err['msg']
        messages.append(f"{loc}: {msg}")
    return "; ".join(messages)
