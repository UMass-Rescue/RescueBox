from typing import Any, Callable, Mapping, Union, get_type_hints

from pydantic import BaseModel
from typing_extensions import assert_never

from rb.lib.errors import BadRequestError
from rb.api.models import (
    InputType,
    NewFileInputType,
    ParameterType,
    ResponseBody,
    TaskSchema,
    BatchDirectoryInput,
    BatchFileInput,
    BatchTextInput,
    DirectoryInput,
    FileInput,
    TextInput,
)


def is_typeddict(cls):
    return isinstance(cls, type) and hasattr(cls, "__annotations__")


def ensure_ml_func_parameters_are_typed_dict(
    ml_function: Callable[[Any, Any], ResponseBody],
):
    hints = get_type_hints(ml_function)
    if not is_typeddict(hints["inputs"]):
        raise BadRequestError("Inputs must be a TypedDict")
    if "parameters" in hints and not is_typeddict(hints["parameters"]):
        raise BadRequestError("Parameters must be a TypedDict")


def ensure_ml_func_hinting_and_task_schemas_are_valid(
    ml_function: Callable[[Any, Any], ResponseBody], task_schema: TaskSchema
):
    hints = get_type_hints(ml_function)
    input_type_hints: Mapping[str, BaseModel] = get_type_hints(hints["inputs"])
    parameters_type_hints: Mapping[str, Union[str, int, float]] = (
        get_type_hints(hints["parameters"]) if "parameters" in hints else {}
    )

    input_schema = task_schema.inputs
    parameters_schema = task_schema.parameters

    input_schema_input_key_to_input_type = {
        inputt.key: inputt.input_type for inputt in input_schema
    }
    parameters_schema_key_to_parameter_type = {
        parameter.key: parameter.value.parameter_type for parameter in parameters_schema
    }

    assert list(input_type_hints.keys()) == list(
        input_schema_input_key_to_input_type.keys()
    ), f"Input schema and Typed Dict for inputs must have the same keys. Input schema keys: {input_schema_input_key_to_input_type.keys()} | Typed Dict keys: {input_type_hints.keys()}"
    assert list(parameters_type_hints.keys()) == list(
        parameters_schema_key_to_parameter_type.keys()
    ), f"Parameter schema and Typed Dict for parameters must have the same keys. Parameter schema keys: {parameters_schema_key_to_parameter_type.keys()} | Typed Dict keys: {parameters_type_hints.keys()}"

    for key in input_schema_input_key_to_input_type:
        input_type_hint = input_type_hints[key]
        input_type = input_schema_input_key_to_input_type[key]
        match input_type:
            case InputType.FILE:
                assert (
                    input_type_hint is FileInput
                ), f"For key {key}, the input type is InputType.FILE, but the TypeDict hint is {input_type_hint}. Change to FileInput."
            case NewFileInputType():
                assert (
                    input_type_hint is FileInput
                ), f"For key {key}, the input type is NewFileInputType, but the TypeDict hint is {input_type_hint}. Change to FileInput."
            case InputType.DIRECTORY:
                assert issubclass(
                    input_type_hint, DirectoryInput
                ), f"For key {key}, the input type is InputType.DIRECTORY, but the TypeDict hint is {input_type_hint}. Change to DirectoryInput."
            case InputType.TEXT:
                assert (
                    input_type_hint is TextInput
                ), f"For key {key}, the input type is InputType.TEXT, but the TypeDict hint is {input_type_hint}. Change to TextInput."
            case InputType.TEXTAREA:
                assert (
                    input_type_hint is TextInput
                ), f"For key {key}, the input type is InputType.TEXTAREA, but the TypeDict hint is {input_type_hint}. Change to TextInput."
            case InputType.BATCHFILE:
                assert (
                    input_type_hint is BatchFileInput
                ), f"For key {key}, the input type is InputType.BATCHFILE, but the TypeDict hint is {input_type_hint}. Change to BatchFileInput."
            case InputType.BATCHTEXT:
                assert (
                    input_type_hint is BatchTextInput
                ), f"For key {key}, the input type is InputType.BATCHTEXT, but the TypeDict hint is {input_type_hint}. Change to BatchTextInput."
            case InputType.BATCHDIRECTORY:
                assert (
                    input_type_hint is BatchDirectoryInput
                ), f"For key {key}, the input type is InputType.BATCHDIRECTORY, but the TypeDict hint is {input_type_hint}. Change to BatchDirectoryInput."
            case _:  # pragma: no cover
                assert_never(input_type)

    for key in parameters_schema_key_to_parameter_type:
        parameter_type_hint = parameters_type_hints[key]
        parameter_type: ParameterType = parameters_schema_key_to_parameter_type[key]  # type: ignore
        match parameter_type:
            case ParameterType.RANGED_FLOAT:
                assert (
                    parameter_type_hint is float
                ), f"For key {key}, the parameter type is ParameterType.RANGED_FLOAT, but the TypeDict hint is {parameter_type_hint}. Change to float."
            case ParameterType.FLOAT:
                assert (
                    parameter_type_hint is float
                ), f"For key {key}, the parameter type is ParameterType.FLOAT, but the TypeDict hint is {parameter_type_hint}. Change to float."
            case ParameterType.ENUM:
                assert (
                    parameter_type_hint is str
                ), f"For key {key}, the parameter type is ParameterType.ENUM, but the TypeDict hint is {parameter_type_hint}. Change to str."
            case ParameterType.TEXT:
                assert (
                    parameter_type_hint is str
                ), f"For key {key}, the parameter type is ParameterType.TEXT, but the TypeDict hint is {parameter_type_hint}. Change to str."
            case ParameterType.RANGED_INT:
                assert (
                    parameter_type_hint is int
                ), f"For key {key}, the parameter type is ParameterType.RANGED_INT, but the TypeDict hint is {parameter_type_hint}. Change to int."
            case ParameterType.INT:
                assert (
                    parameter_type_hint is int
                ), f"For key {key}, the parameter type is ParameterType.INT, but the TypeDict hint is {parameter_type_hint}. Change to int."
            case _:  # pragma: no cover
                assert_never(parameter_type)


# --- Filter helper utilities for plugins ----------------------------------
from typing import List, Optional, Tuple
from pathlib import Path

def extract_filter_id(inputs: dict, parameters: dict) -> Optional[str]:
    """Extract a filter id from parameters or inputs if present."""
    fid = None
    try:
        # Check top-level then _meta container
        fid = parameters.get("filterId") or parameters.get("filter_id") or (parameters.get("_meta") or {}).get("filterId")
    except Exception:
        fid = None

    try:
        ffi = inputs.get("file_filter") if isinstance(inputs, dict) else inputs["file_filter"]
        if isinstance(ffi, dict) and ffi.get("filter_id"):
            fid = fid or ffi.get("filter_id")
        else:
            try:
                attr_fid = getattr(ffi, "filter_id", None)
                if attr_fid:
                    fid = fid or attr_fid
            except Exception:
                pass
    except Exception:
        pass
    return fid


def load_saved_filter(filter_id: str, input_dir: Path) -> Tuple[List[Path], List[str]]:
    """
    Load a persisted filter and return (input_paths, output_patterns).
    Input paths are resolved against input_dir when stored as relative paths.
    """
    from frontend.database.file_filter_store import load_filter

    input_paths: List[Path] = []
    output_patterns: List[str] = []
    if not filter_id:
        return input_paths, output_patterns
    saved = load_filter(filter_id)
    if not saved:
        return input_paths, output_patterns
    spaths = saved.get("paths_json") or []
    if spaths:
        resolved = []
        for p in spaths:
            try:
                rp = Path(p)
                if not rp.is_absolute():
                    rp = Path(input_dir) / rp
                resolved.append(rp)
            except Exception:
                continue
        input_paths = resolved
    output_patterns = saved.get("patterns_json") or []
    return input_paths, output_patterns


def collect_inline_file_filter(inputs: dict, input_dir: Path) -> List[Path]:
    """Collect input file list from uploaded BatchFileInput in the request (inline)."""
    try:
        filter_paths = inputs["file_filter"].files
        if filter_paths:
            return [Path(f.path) for f in filter_paths]
    except Exception:
        pass
    return [Path(f) for f in input_dir.iterdir() if f.is_file()]


def collect_inline_output_patterns(inputs: dict) -> List[str]:
    """Collect output patterns from uploaded output_filter files (inline)."""
    patterns: List[str] = []
    try:
        output_filter_files = inputs.get("output_filter").files
    except Exception:
        output_filter_files = []

    if output_filter_files:
        for pf in output_filter_files:
            try:
                p = Path(pf.path)
                if p.exists():
                    content = p.read_text(encoding="utf-8")
                    for line in content.splitlines():
                        line = line.strip()
                        if line:
                            patterns.append(line)
            except Exception:
                continue
    return patterns

