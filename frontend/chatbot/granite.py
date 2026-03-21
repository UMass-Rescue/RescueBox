import json
import logging
import re
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def parse_fine_tune_tool_response(model_text: str) -> Optional[List[Dict[str, Any]]]:
    tool_calls = []

    pattern = r'<tool_code>\s*(\{.*?\})\s*</tool_code>'
    matches = re.findall(pattern, model_text, re.DOTALL)
    if matches:
        logger.info("Found %d tool call(s) in <tool_code> tags", len(matches))
        for tool_call_json in matches:
            try:
                tool_call = json.loads(tool_call_json)
                tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
        if tool_calls:
            return tool_calls

    json_pattern = r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^}]*\}\s*\}'
    json_matches = re.findall(json_pattern, model_text, re.DOTALL)
    if json_matches:
        for json_str in json_matches:
            try:
                tool_call = json.loads(json_str)
                if 'name' in tool_call and 'arguments' in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
        if tool_calls:
            return tool_calls

    logger.warning("No valid tool calls found in model response")
    logger.info("Model response preview (first 800 chars): %s", model_text[:800] if model_text else "(empty)")
    return None
