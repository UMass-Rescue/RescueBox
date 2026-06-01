import json
import logging
import re
from typing import Any, Optional, List, Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_TOOL_OPEN = "<tool_code>"
_TOOL_CLOSE = "</tool_code>"


def _append_parsed_payload(tool_calls: List[Dict[str, Any]], parsed: Any) -> None:
    """Normalize list / {\"calls\": [...]} / single call dict into tool_calls."""
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict) and "name" in item:
                args = item.get("arguments", {})
                tool_calls.append(
                    {
                        "name": item["name"],
                        "arguments": args if isinstance(args, dict) else {},
                    }
                )
    elif isinstance(parsed, dict):
        if "calls" in parsed and isinstance(parsed["calls"], list):
            _append_parsed_payload(tool_calls, parsed["calls"])
        elif "name" in parsed:
            args = parsed.get("arguments", {})
            tool_calls.append(
                {
                    "name": parsed["name"],
                    "arguments": args if isinstance(args, dict) else {},
                }
            )


def _iter_tool_code_json_strings(model_text: str) -> List[str]:
    """Extract raw JSON payloads between <tool_code> and </tool_code> (any valid JSON)."""
    chunks: List[str] = []
    i = 0
    while True:
        start = model_text.find(_TOOL_OPEN, i)
        if start < 0:
            break
        start += len(_TOOL_OPEN)
        end = model_text.find(_TOOL_CLOSE, start)
        if end < 0:
            logger.warning("Unclosed %s tag in model response", _TOOL_OPEN)
            break
        chunks.append(model_text[start:end].strip())
        i = end + len(_TOOL_CLOSE)
    return chunks


def _scan_json_objects_with_nested_braces(text: str) -> List[str]:
    """
    Find top-level {...} spans by brace depth (handles nested objects in arguments).
    Used as a last-resort fallback when tags are missing.
    """
    spans: List[str] = []
    depth = 0
    start: Optional[int] = None
    for idx, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = idx
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    spans.append(text[start : idx + 1])
                    start = None
    return spans


def parse_fine_tune_tool_response(model_text: str) -> Optional[List[Dict[str, Any]]]:
    if not model_text or not model_text.strip():
        return None

    tool_calls: List[Dict[str, Any]] = []

    for inner in _iter_tool_code_json_strings(model_text):
        if not inner:
            continue
        try:
            parsed = json.loads(inner)
        except json.JSONDecodeError:
            logger.debug("Skip invalid JSON inside tool_code: %s...", inner[:120])
            continue
        before = len(tool_calls)
        _append_parsed_payload(tool_calls, parsed)
        if len(tool_calls) == before:
            logger.debug("tool_code JSON had no recognizable calls: %s...", inner[:120])

    if tool_calls:
        logger.info("Found %d tool call(s) in <tool_code> tags", len(tool_calls))
        return tool_calls

    stripped = model_text.strip()
    try:
        parsed = json.loads(stripped)
        _append_parsed_payload(tool_calls, parsed)
    except json.JSONDecodeError:
        pass

    if tool_calls:
        logger.info("Found %d tool call(s) from raw JSON (no tags)", len(tool_calls))
        return tool_calls

    for json_str in _scan_json_objects_with_nested_braces(model_text):
        try:
            obj = json.loads(json_str)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "name" in obj and "arguments" in obj:
            tool_calls.append(obj)

    if tool_calls:
        logger.info("Found %d tool call(s) via brace-scan fallback", len(tool_calls))
        return tool_calls

    json_pattern = r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^}]*\}\s*\}'
    json_matches = re.findall(json_pattern, model_text, re.DOTALL)
    for json_str in json_matches:
        try:
            tool_call = json.loads(json_str)
            if "name" in tool_call and "arguments" in tool_call:
                tool_calls.append(tool_call)
        except json.JSONDecodeError:
            continue
    if tool_calls:
        logger.info("Found %d tool call(s) via legacy flat-args regex", len(tool_calls))
        return tool_calls

    logger.warning("No valid tool calls found in model response")
    logger.info("Model response preview (first 800 chars): %s", model_text[:800])
    return None
