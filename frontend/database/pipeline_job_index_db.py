"""
Per-pipeline-root SQLite index for linking plugin inputs, outputs, and metadata.

Database path: ``frontend/data/pipeline_index/{user_id}/{root_job_id}.sqlite``
so concurrent pipelines do not share state.

Schema:

- **pipeline_io_links** — canonical model: one **input** file, one **output** file,
  and **metadata_json** (arbitrary k=v object). Use this for new plugins (summarize,
  age–gender, etc.).

- **pipeline_job_steps** — one row per successful job step (endpoint, step job id,
  compact output summary) for pipeline lineage.

- **pipeline_response_rows** — one row per **result item** in the response (each batch
  member, each JSON list element, etc.).

- **image_text_chunks** — legacy table for older DB files; lookups fall back here.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _sanitize_segment(s: str) -> str:
    out = []
    for ch in (s or ""):
        if ch.isalnum() or ch in ("-", "_", "."):
            out.append(ch)
        else:
            out.append("_")
    return "".join(out) or "unknown"


def index_db_path(user_id: str, root_job_id: str) -> Path:
    """Filesystem path for this user + pipeline root job."""
    base = Path(__file__).resolve().parent.parent / "data" / "pipeline_index"
    safe_user = _sanitize_segment(user_id)
    safe_job = _sanitize_segment(root_job_id)
    return base / safe_user / f"{safe_job}.sqlite"


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _ensure_job_steps_schema(conn: sqlite3.Connection) -> None:
    """One row per successful job step in a pipeline (lineage / audit)."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_job_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_job_id TEXT NOT NULL DEFAULT '',
            endpoint TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            detail_json TEXT NOT NULL,
            UNIQUE(step_job_id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pjs_endpoint ON pipeline_job_steps(endpoint)"
    )


def _ensure_response_rows_schema(conn: sqlite3.Connection) -> None:
    """One row per persisted result item from a job response (batch rows, JSON lists, …)."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_response_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_job_id TEXT NOT NULL DEFAULT '',
            endpoint TEXT NOT NULL,
            container TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            output_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(step_job_id, container, ordinal)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_prr_step ON pipeline_response_rows(step_job_id)"
    )


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_io_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_path TEXT NOT NULL,
            output_path TEXT NOT NULL,
            input_path_norm TEXT NOT NULL,
            output_path_norm TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(output_path_norm)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pio_out ON pipeline_io_links(output_path_norm)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pio_in ON pipeline_io_links(input_path_norm)"
    )

    # Legacy: summarize-only index (older DBs); not written by new code paths.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS image_text_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_path TEXT NOT NULL UNIQUE,
            text_path_norm TEXT NOT NULL,
            source_image_path TEXT NOT NULL,
            text_excerpt TEXT,
            provenance_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_norm ON image_text_chunks(text_path_norm)"
    )
    _ensure_job_steps_schema(conn)
    _ensure_response_rows_schema(conn)
    conn.commit()


def _normalize_path(p: str) -> str:
    try:
        return str(Path(p).resolve())
    except OSError:
        return str(Path(p))


def insert_pipeline_job_step(
    user_id: str,
    root_job_id: str,
    step_job_id: Optional[str],
    endpoint: str,
    detail: Dict[str, Any],
) -> None:
    """
    Record a completed pipeline step for lineage (which endpoint ran, when, summary of output shape).

    ``detail`` should stay small (no full file contents); callers should cap or omit large strings.
    """
    if not user_id or not root_job_id or not endpoint:
        return
    sid = (step_job_id or "").strip()
    path = index_db_path(user_id, root_job_id)
    conn = _connect(path)
    try:
        _ensure_schema(conn)
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(detail, ensure_ascii=False)[:24000]
        conn.execute(
            """
            INSERT INTO pipeline_job_steps (step_job_id, endpoint, completed_at, detail_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(step_job_id) DO UPDATE SET
                endpoint = excluded.endpoint,
                completed_at = excluded.completed_at,
                detail_json = excluded.detail_json
            """,
            (sid, endpoint, now, payload),
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.warning("pipeline_job_steps insert failed: %s", e)
    finally:
        conn.close()


def list_pipeline_job_steps(
    user_id: str,
    root_job_id: str,
) -> List[Dict[str, Any]]:
    """Return completed steps for a pipeline root job, oldest first."""
    if not user_id or not root_job_id:
        return []
    db_path = index_db_path(user_id, root_job_id)
    if not db_path.is_file():
        return []
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        cur = conn.execute(
            """
            SELECT step_job_id, endpoint, completed_at, detail_json
            FROM pipeline_job_steps
            ORDER BY id ASC
            """
        )
        out: List[Dict[str, Any]] = []
        for row in cur.fetchall():
            detail: Dict[str, Any]
            try:
                detail = json.loads(row["detail_json"])
            except (json.JSONDecodeError, TypeError):
                detail = {}
            out.append(
                {
                    "step_job_id": row["step_job_id"],
                    "endpoint": row["endpoint"],
                    "completed_at": row["completed_at"],
                    "detail": detail,
                }
            )
        return out
    except sqlite3.Error as e:
        logger.debug("list_pipeline_job_steps failed: %s", e)
        return []
    finally:
        conn.close()


def insert_pipeline_response_rows(
    user_id: str,
    root_job_id: str,
    step_job_id: Optional[str],
    endpoint: str,
    rows: List[Dict[str, Any]],
) -> None:
    """
    Persist flattened response items: each element is
    ``{"container": str, "output_type": str, "payload": dict|list|...}``.

    Replaces any prior rows for the same ``step_job_id`` (one response snapshot per step).
    """
    if not user_id or not root_job_id or not endpoint:
        return
    if not rows:
        return
    sid = (step_job_id or "").strip()
    path = index_db_path(user_id, root_job_id)
    conn = _connect(path)
    try:
        _ensure_schema(conn)
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "DELETE FROM pipeline_response_rows WHERE step_job_id = ?",
            (sid,),
        )
        next_ord: Dict[str, int] = defaultdict(int)
        for r in rows:
            container = str(r.get("container") or "unknown")
            ord_i = next_ord[container]
            next_ord[container] += 1
            ot = str(r.get("output_type") or "unknown")
            payload = r.get("payload")
            if not isinstance(payload, (dict, list, str, int, float, bool)) and payload is not None:
                payload = {"_repr": str(payload)[:8000]}
            try:
                pj = json.dumps(payload, ensure_ascii=False, default=str)
            except (TypeError, ValueError):
                pj = json.dumps({"_error": "unserializable"}, ensure_ascii=False)
            if len(pj) > 65500:
                pj = pj[:65400] + "…<truncated>"
            conn.execute(
                """
                INSERT INTO pipeline_response_rows (
                    step_job_id, endpoint, container, ordinal, output_type, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sid, endpoint, container, ord_i, ot, pj, now),
            )
        conn.commit()
        logger.info(
            "Pipeline response rows: stored %d row(s) for step_job_id=%s endpoint=%s",
            len(rows),
            sid or "(empty)",
            endpoint,
        )
    except sqlite3.Error as e:
        logger.warning("pipeline_response_rows insert failed: %s", e)
    finally:
        conn.close()


def list_pipeline_response_rows(
    user_id: str,
    root_job_id: str,
    step_job_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return persisted response rows, optionally filtered by step_job_id."""
    if not user_id or not root_job_id:
        return []
    db_path = index_db_path(user_id, root_job_id)
    if not db_path.is_file():
        return []
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        if step_job_id is not None:
            cur = conn.execute(
                """
                SELECT step_job_id, endpoint, container, ordinal, output_type, payload_json, created_at
                FROM pipeline_response_rows
                WHERE step_job_id = ?
                ORDER BY container ASC, ordinal ASC
                """,
                ((step_job_id or "").strip(),),
            )
        else:
            cur = conn.execute(
                """
                SELECT step_job_id, endpoint, container, ordinal, output_type, payload_json, created_at
                FROM pipeline_response_rows
                ORDER BY id ASC
                """
            )
        out: List[Dict[str, Any]] = []
        for row in cur.fetchall():
            try:
                payload = json.loads(row["payload_json"])
            except (json.JSONDecodeError, TypeError):
                payload = {}
            out.append(
                {
                    "step_job_id": row["step_job_id"],
                    "endpoint": row["endpoint"],
                    "container": row["container"],
                    "ordinal": row["ordinal"],
                    "output_type": row["output_type"],
                    "payload": payload,
                    "created_at": row["created_at"],
                }
            )
        return out
    except sqlite3.Error as e:
        logger.debug("list_pipeline_response_rows failed: %s", e)
        return []
    finally:
        conn.close()


def insert_pipeline_io_links(
    user_id: str,
    root_job_id: str,
    rows: List[Dict[str, Any]],
) -> None:
    """
    Insert or replace rows: each item has ``input_path``, ``output_path``, and
    ``metadata`` (dict, stored as JSON k=v).

    Downstream steps typically join on ``output_path`` to recover ``input_path``
    and metadata.
    """
    if not rows or not user_id or not root_job_id:
        return
    path = index_db_path(user_id, root_job_id)
    conn = _connect(path)
    try:
        _ensure_schema(conn)
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        for r in rows:
            inp = str(r.get("input_path") or "").strip()
            outp = str(r.get("output_path") or "").strip()
            if not inp or not outp:
                continue
            meta = r.get("metadata")
            if not isinstance(meta, dict):
                meta = {}
            conn.execute(
                """
                INSERT INTO pipeline_io_links (
                    input_path, output_path, input_path_norm, output_path_norm,
                    metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(output_path_norm) DO UPDATE SET
                    input_path = excluded.input_path,
                    output_path = excluded.output_path,
                    input_path_norm = excluded.input_path_norm,
                    metadata_json = excluded.metadata_json,
                    created_at = excluded.created_at
                """,
                (
                    inp,
                    outp,
                    _normalize_path(inp),
                    _normalize_path(outp),
                    json.dumps(meta, ensure_ascii=False),
                    now,
                ),
            )
        conn.commit()
    except sqlite3.Error as e:
        logger.warning("pipeline_io_links insert failed: %s", e)
        raise
    finally:
        conn.close()


def insert_chunks(
    user_id: str,
    root_job_id: str,
    rows: List[Dict[str, Any]],
) -> None:
    """
    Backward-compatible insert for summarize-style rows: ``text_path``,
    ``source_image_path``, optional ``text_excerpt``, ``provenance`` dict.

    Writes to **pipeline_io_links** only (input = source image, output = text file);
    metadata merges provenance + ``text_excerpt`` when present.
    """
    if not rows or not user_id or not root_job_id:
        return
    generic: List[Dict[str, Any]] = []
    for r in rows:
        tp = str(r.get("text_path") or "")
        si = str(r.get("source_image_path") or "")
        if not tp or not si:
            continue
        excerpt = (r.get("text_excerpt") or "")[:20000]
        prov = r.get("provenance") or {}
        if not isinstance(prov, dict):
            prov = {"raw": prov}
        meta = dict(prov)
        if excerpt:
            meta["text_excerpt"] = excerpt
        meta.setdefault("link_kind", "image_summary_text")
        generic.append(
            {
                "input_path": si,
                "output_path": tp,
                "metadata": meta,
            }
        )
    insert_pipeline_io_links(user_id, root_job_id, generic)


def lookup_input_for_output(
    user_id: str,
    root_job_id: str,
    output_path: str,
) -> Optional[str]:
    """
    Return **input_path** for a stored row keyed by **output_path** (e.g. summary
    ``.txt`` or any plugin output path), or None.
    """
    if not user_id or not root_job_id or not output_path:
        return None
    db_path = index_db_path(user_id, root_job_id)
    if not db_path.is_file():
        return None
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        norm = _normalize_path(output_path)
        cur = conn.execute(
            "SELECT input_path FROM pipeline_io_links WHERE output_path_norm = ? LIMIT 1",
            (norm,),
        )
        row = cur.fetchone()
        if row:
            return str(row["input_path"])
        cur = conn.execute(
            "SELECT input_path FROM pipeline_io_links WHERE output_path = ? LIMIT 1",
            (output_path,),
        )
        row = cur.fetchone()
        if row:
            return str(row["input_path"])
        # Legacy image_text_chunks: output was "text" summary path → source image
        cur = conn.execute(
            "SELECT source_image_path FROM image_text_chunks WHERE text_path_norm = ? LIMIT 1",
            (norm,),
        )
        row = cur.fetchone()
        if row:
            return str(row["source_image_path"])
        cur = conn.execute(
            "SELECT source_image_path FROM image_text_chunks WHERE text_path = ? LIMIT 1",
            (output_path,),
        )
        row = cur.fetchone()
        if row:
            return str(row["source_image_path"])
        return None
    except sqlite3.Error as e:
        logger.debug("pipeline_io_links lookup failed: %s", e)
        return None
    finally:
        conn.close()


def lookup_source_image(
    user_id: str,
    root_job_id: str,
    text_path: str,
) -> Optional[str]:
    """Alias: summary text file path → source image path (uses ``lookup_input_for_output``)."""
    return lookup_input_for_output(user_id, root_job_id, text_path)


def lookup_metadata_for_output(
    user_id: str,
    root_job_id: str,
    output_path: str,
) -> Optional[Dict[str, Any]]:
    """Return parsed metadata JSON for a row keyed by output_path, if present."""
    if not user_id or not root_job_id or not output_path:
        return None
    db_path = index_db_path(user_id, root_job_id)
    if not db_path.is_file():
        return None
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        norm = _normalize_path(output_path)
        cur = conn.execute(
            "SELECT metadata_json FROM pipeline_io_links WHERE output_path_norm = ? LIMIT 1",
            (norm,),
        )
        row = cur.fetchone()
        if not row:
            cur = conn.execute(
                "SELECT metadata_json FROM pipeline_io_links WHERE output_path = ? LIMIT 1",
                (output_path,),
            )
            row = cur.fetchone()
        if not row:
            return None
        raw = row["metadata_json"]
        return json.loads(raw) if isinstance(raw, str) else None
    except (sqlite3.Error, json.JSONDecodeError, TypeError) as e:
        logger.debug("lookup_metadata_for_output failed: %s", e)
        return None
    finally:
        conn.close()
