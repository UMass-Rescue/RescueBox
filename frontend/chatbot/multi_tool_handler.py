# frontend/chatbot/multi_tool_handler.py
"""
Multiple Tool Call Handler

This module handles sequential execution of multiple tool calls from the Granite model.
It supports:
- Sequential execution of tool calls
- Output chaining (output from first call -> input to second call)
- Result history tracking
- User input between calls (optional)
- Display of all results with history view
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from rb.api.models import ResponseBody, TaskSchema, RequestBody, InputType
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.utils import normalize_arguments
from frontend.utils.validators import validate_request_body

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


def extract_batch_file_items(response_body: ResponseBody) -> List[Dict[str, Any]]:
    """
    Extract path and metadata from each FileResponse in a BatchFileResponse.
    Returns list of dicts: [{"path": str, "metadata": dict}, ...].
    Returns empty list if not BatchFileResponse or no files.
    """
    from rb.api.models import BatchFileResponse, FileResponse
    try:
        root = response_body.root
        if not isinstance(root, BatchFileResponse) or not root.files:
            return []
        items = []
        for fr in root.files:
            if isinstance(fr, FileResponse):
                items.append({
                    "path": str(fr.path),
                    "metadata": dict(fr.metadata) if fr.metadata else {},
                })
        return items
    except Exception as e:
        logger.warning("Error extracting batch file items: %s", e)
        return []


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


def apply_metadata_filter(items: List[Dict[str, Any]], criteria_str: str) -> List[str]:
    """
    Filter items by metadata criteria. criteria_str format: "Key:value" or "Key=value", comma-separated.
    Supports both colon and equals: "Gender:Female" or "Gender=Female".
    E.g. "Gender:Female, Age:>30" keeps items where Gender==Female and Age>30.
    Age values from Age/Gender classifier are range strings like "(0-2)", "(25-32)" - we use the
    upper bound for numeric comparisons (e.g. Age=<10 matches "(0-2)", "(4-6)").
    Returns list of paths for items that match. Empty criteria = all items.
    """
    if not criteria_str or not criteria_str.strip():
        return [it["path"] for it in items]
    criteria = [c.strip() for c in criteria_str.split(",") if c.strip()]
    if not criteria:
        return [it["path"] for it in items]
    result = []
    for it in items:
        logger.info("items path has %s", it["path"]) 
        meta = it.get("metadata") or {}
        match = True
        for c in criteria:
            # Support both "Key:value" and "Key=value"
            if "=" in c:
                key, val = c.split("=", 1)
            elif ":" in c:
                key, val = c.split(":", 1)
            else:
                continue
            key = key.strip()
            val = val.strip()
            mval = meta.get(key)
            if mval is None:
                match = False
                break
            mval_str = str(mval)
            key_lower = key.lower()
            # Age from Age/Gender classifier is "(0-2)", "(25-32)" etc - parse for numeric comparison
            age_num = _parse_age_range_for_comparison(mval_str) if key_lower == "age" else None
            logger.info("Metadata mval_str %s", mval_str)
            logger.info(f"The age_num is: {age_num}")
            if val.startswith(">"):
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
                else:
                    match = mval_str == val
            if not match:
                break
        if match:
            result.append(it["path"])
            logger.info("result path is %s", it["path"]) 
    logger.info("Metadata filter applied: %d paths from %d items", len(result), len(items))
    return list(dict.fromkeys(result))  # deduplicate paths


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
    from rb.api.models import BatchDirectoryResponse, DirectoryResponse, BatchFileResponse, FileResponse
    
    try:
        root = response_body.root
        
        # BatchDirectoryResponse
        if isinstance(root, BatchDirectoryResponse) and root.directories:
            output_path = root.directories[0].path
            logger.debug("Extracted output path from BatchDirectoryResponse: %s", output_path)
            return str(Path(output_path).parent) if Path(output_path).is_file() else output_path
        
        # DirectoryResponse
        if isinstance(root, DirectoryResponse):
            output_path = root.path
            logger.debug("Extracted output path from DirectoryResponse: %s", output_path)
            return str(Path(output_path).parent) if Path(output_path).is_file() else output_path
        
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
    logger.info("Attempting to chain output from previous call to current call")
    
    # Extract output path from previous call
    output_path = extract_output_path(previous_output)
    if not output_path:
        logger.debug("No output path found in previous result, skipping chaining")
        return current_arguments
    
    # Find input directory field in current schema
    input_dir_key = None
    for input_schema in current_schema.inputs:
        if input_schema.input_type == InputType.DIRECTORY:
            # Try common names for input directory
            key_lower = input_schema.key.lower()
            if 'input' in key_lower and 'dir' in key_lower:
                input_dir_key = input_schema.key
                break
    
    # Also check arguments for common patterns
    if not input_dir_key:
        for key in current_arguments.keys():
            key_lower = key.lower()
            if 'input' in key_lower and ('dir' in key_lower or 'dataset' in key_lower):
                input_dir_key = key
                break
    
    # Update arguments if input directory found
    if input_dir_key:
        logger.info("Chaining output path '%s' to input '%s'", output_path, input_dir_key)
        current_arguments = current_arguments.copy()
        current_arguments[input_dir_key] = output_path
    else:
        logger.debug("No input directory field found in schema, skipping chaining")
    
    return current_arguments


async def execute_tool_call_sequence(
    tool_calls: List[Dict[str, Any]],
    core: ChatbotCore,
    on_form_needed: Optional[Callable] = None,
    on_result: Optional[Callable] = None,
    on_complete: Optional[Callable] = None,
    chain_outputs: bool = True
) -> MultiToolCallResult:
    """
    Execute multiple tool calls sequentially with optional output chaining.
    
    Note: designed for fully automated workflows without user interaction
    
    This function processes tool calls one by one:
    1. Loads task schema for each call
    2. Chains output from previous call if enabled
    3. Shows form for user input if needed
    4. Submits job and waits for result
    5. Stores result for history
    6. Moves to next call
    
    Args:
        tool_calls: List of tool call dicts with 'endpoint' and 'arguments'
        core: ChatbotCore instance
        on_form_needed: Callback when form is needed (call_index, endpoint, arguments, schema)
        on_result: Callback when result is received (call_index, endpoint, result)
        on_complete: Callback when all calls complete (MultiToolCallResult)
        chain_outputs: Whether to chain outputs between calls
        
    Returns:
        MultiToolCallResult: Result object containing all results and errors
    """
    logger.info("Starting execution of %d tool call(s)", len(tool_calls))
    
    result = MultiToolCallResult()
    previous_output: Optional[ResponseBody] = None
    
    for call_index, tool_call in enumerate(tool_calls):
        endpoint = tool_call['endpoint']
        arguments = tool_call['arguments']
        
        logger.info("Processing tool call %d/%d: %s", call_index + 1, len(tool_calls), endpoint)
        
        try:
            # Load task schema
            task_schema = await core.get_task_schema_from_endpoint(endpoint)
            if not task_schema:
                error_msg = f"Failed to load schema for {endpoint}"
                logger.error(error_msg)
                result.add_result(tool_call, None, error_msg)
                continue
            
            # Chain output from previous call if enabled
            if chain_outputs and previous_output and call_index > 0:
                logger.info("Chaining output from previous call to call %d", call_index + 1)
                arguments = chain_output_to_input(previous_output, arguments, task_schema)
            
            # Convert arguments to initial values
            initial_values = core.convert_arguments_to_initial_values(
                arguments, task_schema, endpoint
            )
            
            # If form callback provided, use it (allows user input/confirmation)
            if on_form_needed:
                logger.debug("Requesting form for call %d", call_index + 1)
                await on_form_needed(call_index, endpoint, initial_values, task_schema)
                # Note: on_form_needed should handle form submission and call on_result
                # This is handled by the caller
                continue
            
            # Otherwise, auto-submit with provided arguments
            logger.debug("Auto-submitting call %d with provided arguments", call_index + 1)
            request_body = validate_request_body(
                {'inputs': initial_values.get('inputs', {}), 'parameters': initial_values.get('parameters', {})},
                task_schema
            )
            
            if isinstance(request_body, dict) and not request_body.get('is_valid', True):
                error_msg = f"Validation failed: {request_body.get('errors', {})}"
                logger.error(error_msg)
                result.add_result(tool_call, None, error_msg)
                continue
            
            if not isinstance(request_body, RequestBody):
                error_msg = "Failed to validate request body"
                logger.error(error_msg)
                result.add_result(tool_call, None, error_msg)
                continue
            
            # Submit job
            response_body = await core.submit_job(request_body, endpoint)
            previous_output = response_body
            result.add_result(tool_call, response_body, None)
            
            # Call result callback
            if on_result:
                await on_result(call_index, endpoint, response_body)
            
            logger.info("Tool call %d completed successfully", call_index + 1)
            
        except Exception as e:
            error_msg = f"Error executing tool call {call_index + 1} ({endpoint}): {str(e)}"
            logger.error(error_msg, exc_info=True)
            result.add_result(tool_call, None, error_msg)
            
            # Continue with next call even if this one failed
            continue
    
    logger.info("Completed execution of %d/%d tool call(s)", result.completed_count, len(tool_calls))
    
    # Call completion callback
    if on_complete:
        await on_complete(result)
    
    return result

