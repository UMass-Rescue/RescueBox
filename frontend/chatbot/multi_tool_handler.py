# frontend/chatbot/multi_tool_handler.py
"""
Helpers for Granite multi-tool and pipeline flows: response coercion, chaining,
metadata filtering, and batch path extraction used by chatbot / jobs UI.

The ``multi_tool_calls`` message path yields sequential forms handled in
``pages/chatbot`` (coordinator ``PipelineHandler``); this module provides the shared
utilities. ``MultiToolCallResult`` aggregates per-step outcomes for callers/tests.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from rb.api.models import ResponseBody, TaskSchema, InputType
from frontend.utils import validate_response_body

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MultiToolCallResult:
    """Result of executing multiple tool calls."""
    
    def __init__(self):
        self.tool_calls: List[Dict[str, Any]] = []
        self.results: List[ResponseBody] = []
        self.errors: List[str] = []
        self.completed_count = 0
    
    def add_result(self, tool_call: Dict, result: Optional[ResponseBody], error: Optional[str] = None):
        """Add a result for a tool call."""
        self.tool_calls.append(tool_call)
        self.results.append(result)
        self.errors.append(error)
        if result:
            self.completed_count += 1


def coerce_pipeline_response(raw: Any) -> Any:
    """
    Normalize a job POST JSON dict into ResponseBody when possible.

    ``ResponseBody(**dict)`` alone can fail or mis-parse some wire shapes; the
    same ``validate_response_body`` path used elsewhere also applies legacy
    ``output_type=batchfile`` handling.
    """
    from rb.api.models import BatchFileResponse

    if isinstance(raw, ResponseBody):
        return raw
    if not isinstance(raw, dict):
        return raw
    validated = validate_response_body(raw)
    if isinstance(validated, ResponseBody):
        return validated
    inner = raw.get("root")
    if isinstance(inner, dict):
        validated_inner = validate_response_body(inner)
        if isinstance(validated_inner, ResponseBody):
            return validated_inner
        # Some APIs wrap only the inner union member
        try:
            return ResponseBody(root=BatchFileResponse.model_validate(inner))
        except Exception:
            pass
    try:
        return ResponseBody(**raw)
    except Exception as e:
        logger.warning(
            "coerce_pipeline_response: could not build ResponseBody (%s); keys=%s",
            e,
            list(raw.keys())[:24],
        )
        return raw


def extract_batch_file_items(response_body: Any) -> List[Dict[str, Any]]:
    """
    Extract path and metadata from each file in a BatchFileResponse-shaped payload.
    Returns list of dicts: [{"path": str, "metadata": dict}, ...].
    Returns empty list if not batch files or no usable file rows.
    Accepts ResponseBody or plain dict (e.g. before coercion).
    """
    from rb.api.models import BatchFileResponse, FileResponse
    try:
        root: Any = None
        if isinstance(response_body, ResponseBody):
            root = response_body.root
        elif isinstance(response_body, dict):
            root = response_body.get("root", response_body)

        files: List[Any] = []
        if isinstance(root, BatchFileResponse) and root.files:
            files = list(root.files)
        elif isinstance(root, dict) and root.get("output_type") == "batchfile":
            files = list(root.get("files") or [])

        if not files:
            return []

        items: List[Dict[str, Any]] = []
        for fr in files:
            if isinstance(fr, FileResponse):
                items.append({
                    "path": Path(fr.path).as_posix(),
                    "metadata": dict(fr.metadata) if fr.metadata else {},
                })
            elif isinstance(fr, dict):
                path = fr.get("path")
                if not path:
                    continue
                meta = fr.get("metadata")
                items.append({
                    "path": Path(path).as_posix(),
                    "metadata": dict(meta) if isinstance(meta, dict) else {},
                })
            else:
                logger.debug("extract_batch_file_items: skipping unknown file entry type=%s", type(fr))

        if not items and files:
            logger.warning(
                "extract_batch_file_items: %d file row(s) present but none produced items (first type=%s)",
                len(files),
                type(files[0]),
            )
        return items
    except Exception as e:
        logger.warning("Error extracting batch file items: %s", e)
        return []


def batch_items_have_age_gender_metadata(items: List[Dict[str, Any]]) -> bool:
    """
    True if any batch row has Age/Gender classifier fields.

    Used to decide whether to show the pipeline "Gender/Age" filter dialog between steps.
    CLIP / image search rows typically only have Query, Similarity, Match, Model — filtering
    those with age-gender criteria would incorrectly drop every file.
    """
    for it in items:
        meta = it.get("metadata") or {}
        for k in meta:
            kl = str(k).lower()
            if kl in ("gender", "age"):
                return True
    return False


def _parse_age_range_for_comparison(mval_str: str) -> Optional[float]:
    """
    Parse age range strings like "(0-2)", "(25-32)", "(60-100)" from Age/Gender classifier.
    Returns the upper bound as float for numeric comparison, or None if not parseable.
    """
    import re
    m = re.match(r"\((\d+)-(\d+)\)", mval_str.strip())
    if m:
        return float(m.group(2))  # upper bound
    return 0


def _meta_get(meta: Dict[str, Any], key: str) -> Optional[Any]:
    """Resolve metadata value with case-insensitive key (Age/Gender classifier uses 'Gender', 'Age')."""
    k = key.strip()
    if k in meta:
        return meta[k]
    kl = k.lower()
    for mk, mv in meta.items():
        if str(mk).lower() == kl:
            return mv
    return None


def apply_metadata_filter(items: List[Dict[str, Any]], criteria_str: str) -> List[str]:
    """
    Filter items by metadata criteria. Comma-separated clauses. Forms:

    * ``Key:value`` or ``Key=value`` — e.g. ``Gender:Female``, ``Age:>30`` (value may start with ``<`` / ``>``).
    * Bare comparison: ``Key < 10``, ``Age<10``, ``Age >= 65`` (spaces optional; ``<=`` / ``>=`` supported).

    Age values from the classifier look like ``(0-2)``, ``(25-32)`` — the upper bound is used for compares.

    Returns list of paths for items that match all clauses. Empty criteria = all items.
    """
    if not criteria_str or not criteria_str.strip():
        paths = [it["path"] for it in items]
        logger.debug(
            "apply_metadata_filter: empty criteria — passing all %d file(s): %s",
            len(paths),
            paths,
        )
        return paths
    criteria = [c.strip() for c in criteria_str.split(",") if c.strip()]
    if not criteria:
        paths = [it["path"] for it in items]
        logger.debug(
            "apply_metadata_filter: no parseable criteria tokens — passing all %d file(s): %s",
            len(paths),
            paths,
        )
        return paths
    logger.info(
        "apply_metadata_filter: criteria_str=%r parsed_clauses=%s evaluating %d item(s)",
        criteria_str,
        criteria,
        len(items),
    )
    result = []
    for it in items:
        meta = it.get("metadata") or {}
        match = True
        for c in criteria:
            bare_cmp: Optional[str] = None
            # Try bare "Key < 10" / "Age >= 25" before "=" — ">=", "<=" contain "=" and must not split on it.
            m = re.match(r"^\s*(\S+)\s*(<=|>=|<|>)\s*(.+)\s*$", c)
            if m:
                key, bare_cmp, val = m.group(1), m.group(2), m.group(3)
            elif ":" in c:
                key, val = c.split(":", 1)
            elif "=" in c:
                key, val = c.split("=", 1)
            else:
                continue
            key = key.strip()
            val = val.strip()
            mval = _meta_get(meta, key)
            if mval is None:
                match = False
                break
            mval_str = str(mval)
            key_lower = key.lower()
            age_num = _parse_age_range_for_comparison(mval_str) if key_lower == "age" else None
            logger.info("Metadata mval_str %s", mval_str)
            logger.info(f"The age_num is: {age_num}")

            if bare_cmp is not None:
                try:
                    cmp_val = float(val)
                except (ValueError, TypeError):
                    match = False
                else:
                    if key_lower == "age":
                        an = _parse_age_range_for_comparison(mval_str)
                        if bare_cmp == "<":
                            match = an < cmp_val
                        elif bare_cmp == ">":
                            match = an > cmp_val
                        elif bare_cmp == "<=":
                            match = an <= cmp_val
                        else:
                            match = an >= cmp_val
                    else:
                        try:
                            n = float(mval_str)
                        except (ValueError, TypeError):
                            match = False
                        else:
                            if bare_cmp == "<":
                                match = n < cmp_val
                            elif bare_cmp == ">":
                                match = n > cmp_val
                            elif bare_cmp == "<=":
                                match = n <= cmp_val
                            else:
                                match = n >= cmp_val
            elif val.startswith(">"):
                try:
                    cmp_val = float(val[1:].strip())
                    if age_num is not None:
                        match = age_num > cmp_val
                    else:
                        match = float(mval_str) > cmp_val
                except (ValueError, TypeError):
                    match = mval_str == val[1:].strip()
            elif val.startswith("<"):
                try:
                    cmp_val = float(val[1:].strip())
                    if age_num is not None:
                        match = age_num < cmp_val
                    else:
                        match = float(mval_str) < cmp_val
                except (ValueError, TypeError):
                    match = mval_str == val[1:].strip()
            else:
                if age_num is not None:
                    try:
                        match = age_num == float(val)
                    except (ValueError, TypeError):
                        match = mval_str == val
                elif key_lower == "gender":
                    match = mval_str.strip().lower() == val.strip().lower()
                else:
                    match = mval_str == val
            if not match:
                break
        if match:
            result.append(it["path"])
        logger.debug(
            "apply_metadata_filter row: path=%s matched=%s metadata=%s",
            it.get("path"),
            match,
            meta,
        )
    result = list(dict.fromkeys(result))
    logger.info(
        "apply_metadata_filter: done — %d matched path(s) of %d: %s",
        len(result),
        len(items),
        result,
    )
    return result


def extract_output_path(response_body: ResponseBody) -> Optional[str]:
    """
    Extract output directory/path from a ResponseBody.
    
    This function attempts to extract the output path from various response types:
    - BatchDirectoryResponse: Returns the first directory path
    - DirectoryResponse: Returns the directory path
    - BatchFileResponse: Returns parent directory of first file (if same dir)
    - FileResponse: Returns parent directory of file
    
    Args:
        response_body: ResponseBody from API call
        
    Returns:
        Optional[str]: Output path if found, None otherwise
    """
    from rb.api.models import (
        BatchDirectoryResponse,
        DirectoryResponse,
        BatchFileResponse,
        BatchTextResponse,
        FileResponse,
        TextResponse,
    )

    try:
        root = response_body.root

        if isinstance(root, BatchTextResponse) and getattr(root, "transcripts_dir", None):
            td = Path(root.transcripts_dir).as_posix()
            logger.debug("Extracted transcripts_dir from BatchTextResponse: %s", td)
            return td

        # UFDR mount: TextResponse value "Mounted at /tmp/case1" — downstream tools use .../files/
        if isinstance(root, TextResponse) and root.value:
            vm = (root.value or "").strip()
            if vm.lower().startswith("mounted at "):
                mp = vm[len("Mounted at ") :].strip()
                if mp:
                    # Don't use resolve() to avoid Windows drive letters/normalization
                    files_root = Path(mp.rstrip("/")) / "files"
                    logger.debug(
                        "Extracted UFDR files root from mount message: %s", files_root.as_posix()
                    )
                    return files_root.as_posix()

        # TextResponse - e.g. image_summary returns JSON array of output file paths
        if isinstance(root, TextResponse) and root.value:
            try:
                import json
                parsed = json.loads(root.value)
                file_list = None
                if isinstance(parsed, dict) and parsed.get("image_summary"):
                    file_list = parsed.get("files")
                elif isinstance(parsed, list):
                    file_list = parsed
                if file_list and isinstance(file_list, list):
                    first_path = file_list[0]
                    if isinstance(first_path, str):
                        output_path = Path(first_path).parent.as_posix()
                        logger.debug("Extracted output path from TextResponse (file list): %s", output_path)
                        return output_path
            except (json.JSONDecodeError, TypeError, IndexError):
                pass

        # BatchDirectoryResponse
        if isinstance(root, BatchDirectoryResponse) and root.directories:
            output_path = root.directories[0].path
            logger.debug("Extracted output path from BatchDirectoryResponse: %s", output_path)
            return Path(output_path).parent.as_posix() if Path(output_path).is_file() else Path(output_path).as_posix()
        
        # DirectoryResponse
        if isinstance(root, DirectoryResponse):
            output_path = root.path
            logger.debug("Extracted output path from DirectoryResponse: %s", output_path)
            return Path(output_path).parent.as_posix() if Path(output_path).is_file() else Path(output_path).as_posix()
        
        # BatchFileResponse - use parent directory of first file
        if isinstance(root, BatchFileResponse) and root.files:
            first_file = root.files[0]
            output_path = Path(first_file.path).parent
            logger.debug("Extracted output path from BatchFileResponse: %s", output_path)
            # Normalize path separators for cross-platform compatibility
            return output_path.as_posix()
        
        # FileResponse - use parent directory
        if isinstance(root, FileResponse):
            output_path = Path(root.path).parent
            logger.debug("Extracted output path from FileResponse: %s", output_path)
            # Normalize path separators for cross-platform compatibility
            return output_path.as_posix()
        
        logger.debug("Could not extract output path from response")
        return None
    except Exception as e:
        logger.warning("Error extracting output path: %s", str(e))
        return None


def chain_output_to_input(
    previous_output: ResponseBody,
    current_arguments: Dict[str, Any],
    current_schema: TaskSchema
) -> Dict[str, Any]:
    """
    Chain output from previous tool call to input of next tool call.
    
    This function attempts to use the output path from the previous call as
    input directory for the next call, if applicable.
    
    Args:
        previous_output: ResponseBody from previous tool call
        current_arguments: Arguments for current tool call
        current_schema: TaskSchema for current tool call
        
    Returns:
        Dict[str, Any]: Updated arguments with chained output if applicable
    """
    logger.debug("Attempting to chain output from previous call to current call")
    
    # Extract output path from previous call
    output_path = extract_output_path(previous_output)
    if not output_path:
        logger.info("No output path found in previous result, skipping chaining")
        return current_arguments
    
    # Find input directory field in current schema
    input_dir_key = None
    output_dir_key = None
    for input_schema in current_schema.inputs:
        if input_schema.input_type == InputType.DIRECTORY:
            # Try common names for input directory
            key_lower = input_schema.key.lower()
            if 'input' in key_lower and 'dir' in key_lower:
                input_dir_key = input_schema.key
            if 'output' in key_lower and 'dir' in key_lower:
                output_dir_key = input_schema.key

    
    # Also check arguments for common patterns
    if not input_dir_key:
        for key in current_arguments.keys():
            key_lower = key.lower()
            if 'input' in key_lower and ('dir' in key_lower or 'dataset' in key_lower):
                input_dir_key = key
                break
    
    # Update arguments if input directory found
    if input_dir_key:
        logger.info("Chaining path '%s' to input '%s'", output_path, input_dir_key)
        current_arguments = current_arguments.copy()
        current_arguments[input_dir_key] = output_path
        # at least the path is valid in case user forgets to pay attention to this
        current_arguments[output_dir_key] = output_path
        logger.info("Chaining path '%s' to output '%s'", output_path, output_dir_key)
        # text_summarization/summarize: default output_dir next to transcripts (sibling folder)
        for inp in current_schema.inputs:
            if inp.input_type != InputType.DIRECTORY:
                continue
            k = inp.key
            if k == input_dir_key:
                continue
            kl = k.lower()
            if "output" in kl and "dir" in kl:
                if not current_arguments.get(k):
                    suggested = Path(output_path).parent / "text_summary"
                    current_arguments[k] = suggested.as_posix()
                    logger.debug(
                        "Chained default %s for summarize pipeline: %s", k, current_arguments[k]
                    )
                break

        # If previous response is TextResponse with file list, also inject file_filter for pipelines
        # (e.g. image_summary -> text_embeddings)
        from rb.api.models import TextResponse
        root = previous_output.root
        if isinstance(root, TextResponse) and root.value:
            try:
                import json
                parsed = json.loads(root.value)
                if isinstance(parsed, dict) and parsed.get("image_summary"):
                    raw_paths = parsed.get("files") or []
                elif isinstance(parsed, list):
                    raw_paths = parsed
                else:
                    raw_paths = []
                if raw_paths:
                    file_paths = [p for p in raw_paths if isinstance(p, str)]
                    if file_paths:
                        # GET .../task_schema often omits file_filter (for_public_api); POST still accepts it.
                        current_arguments["file_filter"] = {
                            "files": [{"path": p} for p in file_paths]
                        }
                        logger.info(
                            "Chained %d file(s) to file_filter from prior TextResponse",
                            len(file_paths),
                        )
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass
    else:
        logger.debug("No input directory field found in schema, skipping chaining")

    return current_arguments

