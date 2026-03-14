"""
Persistent prompt filter store.

Provides simple helpers to create/load/delete/list persisted filters in the jobs DB.
This module intentionally keeps a small, sync API that uses the existing jobs DB
file (same SQLite file used by JobDB).
"""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from frontend.database.job_db import get_job_db

logger = logging.getLogger(__name__)


def _get_conn() -> sqlite3.Connection:
    db = get_job_db()
    return db.connect()


def create_filter(
    name: Optional[str] = None,
    input_dir: Optional[Union[str, Path]] = None,
    paths: Optional[List[Union[str, Path]]] = None,
    patterns: Optional[List[Union[str, int, float]]] = None,
    filter_type: str = "input",
    owner_id: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a persisted filter record and return its id (UUID string).
    """
    conn = _get_conn()
    fid = f"FILTER_{uuid.uuid4().hex}"
    now = datetime.now().isoformat()
    paths_json = json.dumps([str(Path(p)) for p in paths]) if paths else None
    patterns_json = json.dumps(patterns) if patterns else None
    metadata_json = json.dumps(metadata) if metadata else None
    sql = """
    INSERT INTO file_filters (id, name, input_dir, filter_type, paths_json, patterns_json, owner_id, source, metadata, is_active, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    """
    params = (fid, name, str(input_dir) if input_dir else None, filter_type, paths_json, patterns_json, owner_id, source, metadata_json, now, now)
    conn.execute(sql, params)
    conn.commit()
    logger.info("Created filter %s name=%s", fid, name)
    return fid


def load_filter(filter_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a persisted filter by id. Returns dict or None if not found.
    """
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM file_filters WHERE id = ?", (filter_id,))
    row = cur.fetchone()
    if not row:
        return None
    cols = [c[0] for c in cur.description]
    data = dict(zip(cols, row))
    # parse JSON fields
    if data.get("paths_json"):
        try:
            data["paths_json"] = json.loads(data["paths_json"])
        except Exception:
            data["paths_json"] = []
    else:
        data["paths_json"] = []
    if data.get("patterns_json"):
        try:
            data["patterns_json"] = json.loads(data["patterns_json"])
        except Exception:
            data["patterns_json"] = []
    else:
        data["patterns_json"] = []
    if data.get("metadata"):
        try:
            data["metadata"] = json.loads(data["metadata"])
        except Exception:
            data["metadata"] = {}
    else:
        data["metadata"] = {}
    return data


def list_filters(owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = _get_conn()
    if owner_id:
        cur = conn.execute("SELECT * FROM file_filters WHERE owner_id = ? ORDER BY created_at DESC", (owner_id,))
    else:
        cur = conn.execute("SELECT * FROM file_filters ORDER BY created_at DESC")
    rows = cur.fetchall()
    result = []
    cols = [c[0] for c in cur.description]
    for row in rows:
        data = dict(zip(cols, row))
        # parse JSON lightly
        try:
            data["paths_json"] = json.loads(data.get("paths_json") or "[]")
        except Exception:
            data["paths_json"] = []
        try:
            data["patterns_json"] = json.loads(data.get("patterns_json") or "[]")
        except Exception:
            data["patterns_json"] = []
        result.append(data)
    return result


def delete_filter(filter_id: str) -> bool:
    conn = _get_conn()
    cur = conn.execute("DELETE FROM file_filters WHERE id = ?", (filter_id,))
    conn.commit()
    return cur.rowcount > 0


def resolve_filter_for_job(batch_file_input: Any, input_dir: Path, persist_if_requested: bool = False, owner_id: Optional[str] = None) -> Tuple[List[Path], Optional[str]]:
    """
    Resolve input file list from BatchFileInput-like object.
    Returns (list_of_paths, filter_id_if_persisted_or_referenced)
    """
    # If batch_file_input is None, return default: all files under input_dir
    if not batch_file_input:
        return ([p for p in input_dir.iterdir() if p.is_file()], None)

    # If object/dict contains 'filter_id', treat as reference
    if isinstance(batch_file_input, dict) and batch_file_input.get("filter_id"):
        f = load_filter(batch_file_input["filter_id"])
        if f and f.get("paths_json"):
            resolved = [input_dir.joinpath(p).resolve() for p in f["paths_json"]]
            return (resolved, f["id"])
        return ([], None)

    # If it has .files attribute (uploaded files), extract file paths from entries
    files = None
    try:
        files = getattr(batch_file_input, "files", None) or batch_file_input
    except Exception:
        files = None

    if files:
        paths = []
        for entry in files:
            try:
                p = Path(getattr(entry, "path", entry))
                if p.exists():
                    paths.append(p.resolve())
            except Exception:
                continue
        # If persist requested, create filter
        if persist_if_requested and (paths or owner_id):
            rel_paths = [str(p.relative_to(input_dir)) if input_dir in p.parents or p==input_dir else str(p) for p in paths]
            fid = create_filter(name="saved-input-filter", input_dir=str(input_dir), paths=rel_paths, filter_type="input", owner_id=owner_id)
            return (paths, fid)
        return (paths, None)

    return ([p for p in input_dir.iterdir() if p.is_file()], None)


def resolve_output_filter_for_job(output_filter_input: Any, persist_if_requested: bool = False, owner_id: Optional[str] = None) -> Tuple[List[Union[str, int, float]], Optional[str]]:
    """
    Resolve output filter patterns from uploaded files or saved filter references.
    Returns (patterns_list, filter_id_if_persisted_or_referenced)
    """
    if not output_filter_input:
        return ([], None)

    # If reference dict
    if isinstance(output_filter_input, dict) and output_filter_input.get("filter_id"):
        f = load_filter(output_filter_input["filter_id"])
        if f and f.get("patterns_json"):
            return (f["patterns_json"], f["id"])
        return ([], None)

    files = None
    try:
        files = getattr(output_filter_input, "files", None) or output_filter_input
    except Exception:
        files = None

    patterns: List[Union[str, int, float]] = []
    if files:
        for entry in files:
            try:
                p = Path(getattr(entry, "path", entry))
                if p.exists():
                    txt = p.read_text(encoding="utf-8")
                    for line in txt.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        # Try numeric parse
                        try:
                            if "." in line:
                                val = float(line)
                            else:
                                val = int(line)
                            patterns.append(val)
                        except Exception:
                            patterns.append(line)
            except Exception:
                continue
        if persist_if_requested and (patterns or owner_id):
            fid = create_filter(name="saved-output-filter", patterns=patterns, filter_type="output", owner_id=owner_id)
            return (patterns, fid)
        return (patterns, None)

    return ([], None)


def create_composite_filter(paths: Optional[List[Union[str, Path]]] = None, patterns: Optional[List[Union[str, int, float]]] = None, name: Optional[str] = None, input_dir: Optional[Union[str, Path]] = None, owner_id: Optional[str] = None) -> str:
    rel_paths = [str(p) for p in paths] if paths else None
    return create_filter(name=name, input_dir=str(input_dir) if input_dir else None, paths=rel_paths, patterns=patterns, filter_type="composite", owner_id=owner_id)

