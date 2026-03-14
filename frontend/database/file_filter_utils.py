"""
Utility helpers used by job-runner and plugins to apply persisted filters.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union

from frontend.database.file_filter_store import load_filter
from frontend.database.job_db import get_job_db
from frontend.database.file_filter_store import (
    resolve_filter_for_job,
    resolve_output_filter_for_job,
    create_composite_filter,
)

logger = logging.getLogger(__name__)


def set_job_filter(job_db, job_uid: str, *, filter_id: Optional[str] = None, owner_id: Optional[str] = None, clear: bool = False) -> bool:
    """
    Associate a saved filter id with an existing job record.
    This performs a direct SQL update to avoid async round-trips.
    """
    conn = job_db.connect()
    if clear:
        cur = conn.execute("UPDATE jobs SET filterId = NULL WHERE uid = ?", (job_uid,))
    else:
        cur = conn.execute("UPDATE jobs SET filterId = ? WHERE uid = ?", (filter_id, job_uid))
    conn.commit()
    return cur.rowcount > 0


def get_job_filters(job_db, job_uid: str) -> dict:
    """
    Return resolved filter information for a job:
      - filter_id
      - input_paths: List[Path]
      - output_patterns: List[Union[str,int,float]]
      - metadata: dict
    """
    conn = job_db.connect()
    cur = conn.execute("SELECT request, filterId FROM jobs WHERE uid = ?", (job_uid,))
    row = cur.fetchone()
    if not row:
        return {"filter_id": None, "input_paths": [], "output_patterns": [], "metadata": {}}
    request_json, filter_id = row[0], row[1]
    input_paths = []
    output_patterns = []
    metadata = {}
    if filter_id:
        f = load_filter(filter_id)
        if f:
            base_dir = Path(f.get("input_dir")) if f.get("input_dir") else None
            if f.get("paths_json") and base_dir:
                input_paths = [Path(base_dir) / Path(p) for p in f.get("paths_json", [])]
            else:
                input_paths = [Path(p) for p in f.get("paths_json", [])]
            output_patterns = f.get("patterns_json", []) or []
            metadata = f.get("metadata", {}) or {}
    else:
        # Backcompat: try to inspect request JSON for inline lists
        try:
            req = json.loads(request_json)
            inputs = req.get("inputs", {})
            # look for file_filter/files list and output_filter
            ff = inputs.get("file_filter")
            of = inputs.get("output_filter")
            # If file_filter provided as inline files, we can't resolve absolute paths reliably here
            # Leave as empty; plugins should handle inline at submit time.
        except Exception:
            pass
    return {"filter_id": filter_id, "input_paths": input_paths, "output_patterns": output_patterns, "metadata": metadata}


def resolve_input_files(input_dir: Path, input_paths: Optional[List[Path]], supported_extensions: Optional[Iterable[str]] = None) -> List[Path]:
    supported = set([e.lower() for e in (supported_extensions or [".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"])])
    if not input_paths:
        return [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in supported]
    resolved = []
    for p in input_paths:
        try:
            pp = Path(p).resolve()
            if input_dir.resolve() in pp.parents or pp == input_dir.resolve():
                if pp.suffix.lower() in supported:
                    resolved.append(pp)
        except Exception:
            continue
    return resolved


def _match_numeric_range(value: float, pattern: str) -> bool:
    # pattern examples: ">=0.5", "<5", "5..10"
    try:
        if ".." in pattern:
            parts = pattern.split("..", 1)
            low = float(parts[0])
            high = float(parts[1])
            return low <= value <= high
        for op in (">=", "<=", ">", "<", "=="):
            if pattern.startswith(op):
                try:
                    num = float(pattern[len(op):])
                    if op == ">=":
                        return value >= num
                    if op == "<=":
                        return value <= num
                    if op == ">":
                        return value > num
                    if op == "<":
                        return value < num
                    if op == "==":
                        return value == num
                except Exception:
                    return False
    except Exception:
        return False
    return False


def apply_output_filter(output_files: Iterable[Path], output_patterns: List[Union[str, int, float]], mode: str = "substring", case_sensitive: bool = True) -> List[Path]:
    """
    Filter generated summary files by provided patterns.
    mode: 'substring'|'regex'|'numeric_range'
    """
    if not output_patterns:
        return list(output_files)
    matched = []
    for f in output_files:
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for pat in output_patterns:
            if isinstance(pat, (int, float)):
                try:
                    # attempt to extract first float from text for comparison (best-effort)
                    found = re.findall(r"[-+]?\d*\.\d+|\d+", txt)
                    if not found:
                        continue
                    # use first number
                    val = float(found[0])
                    if _match_numeric_range(val, str(pat)):
                        matched.append(f)
                        break
                except Exception:
                    continue
            else:
                sp = str(pat)
                if mode == "substring":
                    hay = txt if case_sensitive else txt.lower()
                    need = sp if case_sensitive else sp.lower()
                    if need in hay:
                        matched.append(f)
                        break
                elif mode == "regex":
                    try:
                        flags = 0 if case_sensitive else re.IGNORECASE
                        if re.search(sp, txt, flags=flags):
                            matched.append(f)
                            break
                    except re.error:
                        continue
        # end patterns loop
    return matched


def parse_output_pattern(pattern_str: str) -> Union[dict, str, float, int]:
    """
    Parse a pattern string into a structured form.
    """
    s = pattern_str.strip()
    # numeric range shorthand
    if ".." in s or any(s.startswith(op) for op in (">=", "<=", ">", "<", "==")):
        return {"type": "range", "value": s}
    # try number
    try:
        if "." in s:
            return float(s)
        return int(s)
    except Exception:
        return {"type": "substring", "value": s}


def process_prompt_for_filters(prompt: str, tool_call: dict, input_dir: Optional[Path] = None, owner_id: Optional[str] = None,
     persist_if_requested: bool = True) -> Optional[str]:
    """
    Inspect the tool_call and prompt to resolve input/output filters.
    Returns a single filter_id if any persisted or referenced filter is found/created.
    Does not persist unless `persist_if_requested` is True or the tool_call references an existing saved filter.
    """
    # Try to find batch/file inputs in tool_call arguments
    args = tool_call.get("arguments", {}) if tool_call else {}
    # Resolve input list
    try:
        input_paths, input_fid = resolve_filter_for_job(args.get("file_filter") or args.get("input_files"), input_dir or Path("."), persist_if_requested=False, owner_id=owner_id)
    except Exception:
        input_paths, input_fid = ([], None)

    # Resolve output patterns
    try:
        output_patterns, output_fid = resolve_output_filter_for_job(args.get("output_filter") or args.get("output_patterns"), persist_if_requested=False, owner_id=owner_id)
    except Exception:
        output_patterns, output_fid = ([], None)

    # If the tool_call already referenced persisted filters, prefer those ids
    if input_fid and output_fid:
        # If both persisted and equal, return that id; if different and persist requested, create composite
        if input_fid == output_fid:
            return input_fid
        if persist_if_requested:
            # load paths and patterns and create composite
            inp = load_filter(input_fid)
            out = load_filter(output_fid)
            paths = inp.get("paths_json", []) if inp else None
            patterns = out.get("patterns_json", []) if out else None
            return create_composite_filter(paths=paths, patterns=patterns, name="composite-from-prompt", input_dir=inp.get("input_dir") if inp else input_dir, owner_id=owner_id)
        # otherwise prefer input fid
        return input_fid
    if input_fid:
        return input_fid
    if output_fid:
        return output_fid

    # No existing persisted filters; if persist requested and there are input_paths or output_patterns, persist accordingly
    if persist_if_requested and (input_paths or output_patterns):
        return create_composite_filter(paths=input_paths if input_paths else None, patterns=output_patterns if output_patterns else None, name="saved-from-prompt", input_dir=str(input_dir) if input_dir else None, owner_id=owner_id)

    # No filter persisted/resolved
    return None

