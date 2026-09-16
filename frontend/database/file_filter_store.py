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
from typing import Any

from frontend.database.db_exceptions import DB_ERRORS
from frontend.database.job_db import get_job_db
from frontend.database.schemas import (
    file_filters_runtime_create_statements,
    file_filters_runtime_index_statements,
)

logger = logging.getLogger(__name__)


def _json_loads_or(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except DB_ERRORS:
        return default


def _parse_pattern_line(line: str):
    line = line.strip()
    if not line:
        return None
    try:
        if "." in line:
            return float(line)
        return int(line)
    except DB_ERRORS:
        return line


def _patterns_from_file(path: Path) -> list[str | int | float]:
    patterns: list[str | int | float] = []
    txt = path.read_text(encoding="utf-8")
    for line in txt.splitlines():
        parsed = _parse_pattern_line(line)
        if parsed is not None:
            patterns.append(parsed)
    return patterns


def _get_conn(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    if conn is not None:
        resolved = conn
    else:
        db = get_job_db()
        resolved = db.connect()
    _ensure_file_filters_schema(resolved)
    return resolved


def _ensure_file_filters_schema(conn: sqlite3.Connection) -> None:
    for statement in file_filters_runtime_create_statements():
        conn.execute(statement.strip())
    for statement in file_filters_runtime_index_statements():
        conn.execute(statement.strip())


def create_filter(
    name: str | None = None,
    input_dir: str | Path | None = None,
    paths: list[str | Path] | None = None,
    patterns: list[str | int | float] | None = None,
    filter_type: str = "input",
    owner_id: str | None = None,
    source: str | None = None,
    metadata: dict[str, Any] | None = None,
    conn: sqlite3.Connection | None = None,
) -> str:
    """
    Create a persisted filter record and return its id (UUID string).
    """
    conn = _get_conn(conn)
    fid = f"FILTER_{uuid.uuid4().hex}"
    now = datetime.now().isoformat()
    paths_json = json.dumps([str(Path(p)) for p in paths]) if paths else None
    patterns_json = json.dumps(patterns) if patterns else None
    metadata_json = json.dumps(metadata) if metadata else None
    sql = """
    INSERT INTO file_filters (id, name, input_dir, filter_type, paths_json, patterns_json, owner_id, source, metadata, is_active, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    """
    params = (
        fid,
        name,
        str(input_dir) if input_dir else None,
        filter_type,
        paths_json,
        patterns_json,
        owner_id,
        source,
        metadata_json,
        now,
        now,
    )
    conn.execute(sql, params)
    conn.commit()
    logger.info("Created filter %s name=%s", fid, name)
    return fid


def load_filter(
    filter_id: str, conn: sqlite3.Connection | None = None
) -> dict[str, Any] | None:
    """
    Load a persisted filter by id. Returns dict or None if not found.
    """
    conn = _get_conn(conn)
    cur = conn.execute("SELECT * FROM file_filters WHERE id = ?", (filter_id,))
    row = cur.fetchone()
    if not row:
        return None
    cols = [c[0] for c in cur.description]
    data = dict(zip(cols, row))
    # parse JSON fields
    data["paths_json"] = _json_loads_or(data.get("paths_json"), [])
    data["patterns_json"] = _json_loads_or(data.get("patterns_json"), [])
    data["metadata"] = _json_loads_or(data.get("metadata"), {})
    return data


def list_filters(
    owner_id: str | None = None, conn: sqlite3.Connection | None = None
) -> list[dict[str, Any]]:
    conn = _get_conn(conn)
    if owner_id:
        cur = conn.execute(
            "SELECT * FROM file_filters WHERE owner_id = ? ORDER BY created_at DESC",
            (owner_id,),
        )
    else:
        cur = conn.execute("SELECT * FROM file_filters ORDER BY created_at DESC")
    rows = cur.fetchall()
    result = []
    cols = [c[0] for c in cur.description]
    for row in rows:
        data = dict(zip(cols, row))
        # parse JSON lightly
        data["paths_json"] = _json_loads_or(data.get("paths_json") or "[]", [])
        data["patterns_json"] = _json_loads_or(data.get("patterns_json") or "[]", [])
        result.append(data)
    return result


def delete_filter(filter_id: str, conn: sqlite3.Connection | None = None) -> bool:
    conn = _get_conn(conn)
    cur = conn.execute("DELETE FROM file_filters WHERE id = ?", (filter_id,))
    conn.commit()
    return cur.rowcount > 0


def resolve_filter_for_job(
    batch_file_input: Any,
    input_dir: Path,
    persist_if_requested: bool = False,
    owner_id: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> tuple[list[Path], str | None]:
    """
    Resolve input file list from BatchFileInput-like object.
    Returns (list_of_paths, filter_id_if_persisted_or_referenced)
    """
    # If batch_file_input is None, return default: all files under input_dir
    if not batch_file_input:
        return ([p for p in input_dir.iterdir() if p.is_file()], None)

    # If object/dict contains 'filter_id', treat as reference
    if isinstance(batch_file_input, dict) and batch_file_input.get("filter_id"):
        f = load_filter(batch_file_input["filter_id"], conn=conn)
        if f and f.get("paths_json"):
            resolved = [input_dir.joinpath(p).resolve() for p in f["paths_json"]]
            return (resolved, f["id"])
        return ([], None)

    # If it has .files attribute (uploaded files), extract file paths from entries
    files = None
    try:
        files = getattr(batch_file_input, "files", None) or batch_file_input
    except DB_ERRORS:
        files = None

    if files:
        paths = []
        for entry in files:
            try:
                p = Path(getattr(entry, "path", entry))
                if p.exists():
                    paths.append(p.resolve())
            except DB_ERRORS:
                continue
        # If persist requested, create filter
        if persist_if_requested and (paths or owner_id):
            rel_paths = [
                (
                    str(p.relative_to(input_dir))
                    if input_dir in p.parents or p == input_dir
                    else str(p)
                )
                for p in paths
            ]
            fid = create_filter(
                name="saved-input-filter",
                input_dir=str(input_dir),
                paths=rel_paths,
                filter_type="input",
                owner_id=owner_id,
                conn=conn,
            )
            return (paths, fid)
        return (paths, None)

    return ([p for p in input_dir.iterdir() if p.is_file()], None)


def resolve_output_filter_for_job(
    output_filter_input: Any,
    persist_if_requested: bool = False,
    owner_id: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> tuple[list[str | int | float], str | None]:
    """
    Resolve output filter patterns from uploaded files or saved filter references.
    Returns (patterns_list, filter_id_if_persisted_or_referenced)
    """
    if not output_filter_input:
        return ([], None)

    # If reference dict
    if isinstance(output_filter_input, dict) and output_filter_input.get("filter_id"):
        f = load_filter(output_filter_input["filter_id"], conn=conn)
        if f and f.get("patterns_json"):
            return (f["patterns_json"], f["id"])
        return ([], None)

    files = None
    try:
        files = getattr(output_filter_input, "files", None) or output_filter_input
    except DB_ERRORS:
        files = None

    patterns: list[str | int | float] = []
    if files:
        for entry in files:
            try:
                p = Path(getattr(entry, "path", entry))
                if p.exists():
                    patterns.extend(_patterns_from_file(p))
            except DB_ERRORS:
                continue
        if persist_if_requested and (patterns or owner_id):
            fid = create_filter(
                name="saved-output-filter",
                patterns=patterns,
                filter_type="output",
                owner_id=owner_id,
                conn=conn,
            )
            return (patterns, fid)
        return (patterns, None)

    return ([], None)


def create_composite_filter(
    paths: list[str | Path] | None = None,
    patterns: list[str | int | float] | None = None,
    name: str | None = None,
    input_dir: str | Path | None = None,
    owner_id: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> str:
    rel_paths = [str(p) for p in paths] if paths else None
    return create_filter(
        name=name,
        input_dir=str(input_dir) if input_dir else None,
        paths=rel_paths,
        patterns=patterns,
        filter_type="composite",
        owner_id=owner_id,
        conn=conn,
    )
