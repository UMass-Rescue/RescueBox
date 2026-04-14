"""
Populate per-pipeline SQLite index from plugin outputs.

Rows are stored as **input_path** + **output_path** + **metadata** (k=v JSON) via
``insert_pipeline_io_links`` / ``insert_chunks`` (summarize wrapper). Other plugins
(e.g. age–gender: one row per face with bbox/age/gender in ``metadata``) can call
``insert_pipeline_io_links`` directly after implementation.

Successful jobs also persist **pipeline_response_rows**: one SQLite row per logical
result item (each batch file row, each JSON list element, etc.).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from frontend.database.pipeline_job_index_db import (
    insert_chunks,
    insert_pipeline_io_links,
    insert_pipeline_job_step,
    insert_pipeline_response_rows,
)
from frontend.components.results.image_summary_results_view import (
    source_image_path_from_summary,
)

logger = logging.getLogger(__name__)

_MAX_IO_ROWS_PER_JOB = 500
_MAX_RESPONSE_ROW_ITEMS = 10000

# JSON object keys whose list values are exploded into one DB row per element.
_JSON_LIST_KEYS = frozenset(
    {
        "files",
        "file_pairs",
        "file_pair_rows",
        "results",
        "rows",
        "items",
        "matches",
        "data",
        "hits",
        "segments",
        "documents",
        "chunks",
        "outputs",
        "images",
        "paths",
        "values",
        "entries",
        "records",
        "candidates",
        "predictions",
    }
)


def _sanitize_payload_fragment(obj: Any, depth: int = 0) -> Any:
    if depth > 14:
        return "<max_depth>"
    if isinstance(obj, str):
        if len(obj) > 16000:
            return obj[:16000] + f"...<trunc {len(obj)} chars>"
        return obj
    if isinstance(obj, (int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        items = list(obj.items())
        for k, v in items[:400]:
            sk = str(k)[:200]
            out[sk] = _sanitize_payload_fragment(v, depth + 1)
        if len(obj) > 400:
            out["_truncated_key_count"] = len(obj) - 400
        return out
    if isinstance(obj, list):
        if len(obj) > 5000:
            return [
                _sanitize_payload_fragment(x, depth + 1) for x in obj[:5000]
            ] + [f"<truncated {len(obj) - 5000} list items>"]
        return [_sanitize_payload_fragment(x, depth + 1) for x in obj]
    return str(obj)[:4000]


def _append_response_row(
    out: List[Dict[str, Any]],
    container: str,
    output_type: str,
    payload: Any,
    cap: int,
) -> bool:
    if len(out) >= cap:
        return False
    out.append(
        {
            "container": container,
            "output_type": output_type,
            "payload": _sanitize_payload_fragment(payload),
        }
    )
    return True


def _flatten_json_dict_lists(payload: dict, out: List[Dict[str, Any]], cap: int) -> None:
    handled: set[str] = set()
    for key in _JSON_LIST_KEYS:
        if key not in payload:
            continue
        v = payload[key]
        if isinstance(v, list):
            handled.add(key)
            for item in v:
                if not _append_response_row(
                    out, f"text.json.{key}", "json_item", item, cap
                ):
                    logger.warning(
                        "pipeline_response_rows: cap %s reached while flattening %s",
                        cap,
                        key,
                    )
                    return
    remainder = {k: v for k, v in payload.items() if k not in handled}
    extra_lists: Dict[str, list] = {}
    for k, v in list(remainder.items()):
        if isinstance(v, list) and v:
            extra_lists[k] = v
    for k, v in extra_lists.items():
        remainder.pop(k, None)
        for item in v:
            if not _append_response_row(
                out, f"text.json.{k}", "json_item", item, cap
            ):
                logger.warning(
                    "pipeline_response_rows: cap %s reached (extra list %s)",
                    cap,
                    k,
                )
                return
    if remainder:
        _append_response_row(out, "text.json.remainder", "json_object", remainder, cap)


def _flatten_text_value(value: Any, out: List[Dict[str, Any]], cap: int) -> None:
    if not isinstance(value, str):
        _append_response_row(out, "text.value", "text", {"value": value}, cap)
        return
    if not value.strip():
        _append_response_row(out, "text.value", "text", {"value": ""}, cap)
        return
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        _append_response_row(out, "text.raw", "text", {"value": value[:32000]}, cap)
        return
    if isinstance(parsed, list):
        for item in parsed:
            if not _append_response_row(out, "text.json[]", "json_item", item, cap):
                logger.warning("pipeline_response_rows: cap %s (json array)", cap)
                return
        return
    if isinstance(parsed, dict):
        _flatten_json_dict_lists(parsed, out, cap)
        return
    _append_response_row(out, "text.json", "json_primitive", {"value": parsed}, cap)


def flatten_job_response_to_rows(
    response_data: Any,
    endpoint: str,
    cap: int = _MAX_RESPONSE_ROW_ITEMS,
) -> List[Dict[str, Any]]:
    """
    Produce one logical record per result row: batch members, JSON list elements, etc.
    """
    out: List[Dict[str, Any]] = []
    root = _response_root_dict(response_data)
    if not root:
        if hasattr(response_data, "model_dump"):
            raw = response_data.model_dump(mode="json")
        elif isinstance(response_data, dict):
            raw = response_data
        else:
            _append_response_row(
                out, "raw", "unknown", {"value": str(response_data)[:8000]}, cap
            )
            return out
        _append_response_row(out, "response_wrapper", "dict", raw, cap)
        return out

    ot = str(root.get("output_type") or "unknown")

    if ot == "batchfile":
        files = root.get("files") or []
        if isinstance(files, list):
            for fr in files:
                if not _append_response_row(
                    out,
                    "root.files",
                    "file",
                    fr if isinstance(fr, dict) else {"_item": fr},
                    cap,
                ):
                    logger.warning(
                        "pipeline_response_rows: cap %s (batchfile)", cap
                    )
                    break
    elif ot == "batchtext":
        td = root.get("transcripts_dir")
        if td:
            _append_response_row(
                out, "root", "batchtext_meta", {"transcripts_dir": td}, cap
            )
        texts = root.get("texts") or []
        if isinstance(texts, list):
            for tx in texts:
                if not _append_response_row(
                    out,
                    "root.texts",
                    "text",
                    tx if isinstance(tx, dict) else {"value": tx},
                    cap,
                ):
                    logger.warning(
                        "pipeline_response_rows: cap %s (batchtext)", cap
                    )
                    break
    elif ot == "batchdirectory":
        dirs = root.get("directories") or []
        if isinstance(dirs, list):
            for d in dirs:
                if not _append_response_row(
                    out,
                    "root.directories",
                    "directory",
                    d if isinstance(d, dict) else {"path": d},
                    cap,
                ):
                    logger.warning(
                        "pipeline_response_rows: cap %s (batchdirectory)", cap
                    )
                    break
    elif ot == "text":
        _flatten_text_value(root.get("value"), out, cap)
    elif ot in ("file", "directory", "markdown"):
        _append_response_row(out, "root", ot, root, cap)
    else:
        _append_response_row(out, "root", ot, root, cap)

    return out


def _response_root_dict(response_data: Any) -> Optional[dict]:
    if response_data is None:
        return None
    if hasattr(response_data, "model_dump"):
        d = response_data.model_dump(mode="json")
    elif isinstance(response_data, dict):
        d = response_data
    else:
        return None
    root = d.get("root") if isinstance(d.get("root"), dict) else d
    return root if isinstance(root, dict) else None


def _parse_text_response_value(response_data: Any) -> Optional[str]:
    root = _response_root_dict(response_data)
    if not root or root.get("output_type") != "text":
        return None
    val = root.get("value")
    return val if isinstance(val, str) else None


def _lineage_detail_from_root(root: dict) -> Dict[str, Any]:
    """Compact summary for pipeline_job_steps (no large blobs)."""
    ot = root.get("output_type") or "unknown"
    out: Dict[str, Any] = {"output_type": ot}
    if ot == "text":
        v = root.get("value")
        if isinstance(v, str):
            out["text_value_chars"] = len(v)
    elif ot == "file":
        p = root.get("path")
        if isinstance(p, str) and p.strip():
            out["output_basename"] = p.rsplit("/", 1)[-1]
    elif ot == "batchfile":
        files = root.get("files") or []
        out["file_count"] = len(files) if isinstance(files, list) else 0
    elif ot == "directory":
        p = root.get("path")
        if isinstance(p, str) and p.strip():
            out["path_basename"] = p.rsplit("/", 1)[-1]
    elif ot == "batchtext":
        texts = root.get("texts") or []
        out["text_count"] = len(texts) if isinstance(texts, list) else 0
        td = root.get("transcripts_dir")
        if isinstance(td, str) and td.strip():
            out["transcripts_dir_suffix"] = td[-120:]
    elif ot == "batchdirectory":
        dirs = root.get("directories") or []
        out["directory_count"] = len(dirs) if isinstance(dirs, list) else 0
    elif ot == "markdown":
        v = root.get("value")
        if isinstance(v, str):
            out["markdown_chars"] = len(v)
    return out


def _parse_json_object_from_text_response(response_data: Any) -> Optional[dict]:
    raw = _parse_text_response_value(response_data)
    if not raw:
        return None
    try:
        obj = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    return obj if isinstance(obj, dict) else None


def _is_image_summarize_endpoint(endpoint: str) -> bool:
    el = (endpoint or "").lower()
    return "image_summary" in el and "summarize" in el


def record_pipeline_job_completion(
    user_id: Optional[str],
    root_job_id: Optional[str],
    step_job_id: Optional[str],
    endpoint: str,
    response_data: Any,
) -> None:
    """
    After any successful job: store lineage, **one persisted row per result item** in
    ``pipeline_response_rows``, then I/O links when pairs are available (summarize,
    ``file_pair_rows``, etc.).

    Safe to call for every endpoint; no-ops when user/root ids are missing.
    """
    if not user_id or not root_job_id:
        return
    root = _response_root_dict(response_data)
    detail: Dict[str, Any] = {
        "endpoint": endpoint,
        "step_job_id": step_job_id or "",
        "pipeline_root_job_id": root_job_id,
        "response": _lineage_detail_from_root(root) if root else {"output_type": "unknown"},
    }
    insert_pipeline_job_step(user_id, root_job_id, step_job_id, endpoint, detail)

    flat = flatten_job_response_to_rows(response_data, endpoint)
    if flat:
        insert_pipeline_response_rows(
            user_id, root_job_id, step_job_id, endpoint, flat
        )

    record_image_summary_for_pipeline(user_id, root_job_id, endpoint, response_data)
    _record_generic_file_pair_artifacts(
        user_id, root_job_id, step_job_id, endpoint, response_data
    )


def _record_generic_file_pair_artifacts(
    user_id: str,
    root_job_id: str,
    step_job_id: Optional[str],
    endpoint: str,
    response_data: Any,
) -> None:
    """
    Index ``file_pair_rows`` (with metadata) and non-summarize ``file_pairs`` from JSON text.

    Skips ``file_pairs`` when the payload is image_summary and the endpoint is
    summarize-images (handled by :func:`record_image_summary_for_pipeline`).
    """
    root = _response_root_dict(response_data)
    rows: List[Dict[str, Any]] = []

    if root and root.get("output_type") == "batchfile":
        files = root.get("files") or []
        if isinstance(files, list):
            for fr in files[:_MAX_IO_ROWS_PER_JOB]:
                if not isinstance(fr, dict):
                    continue
                outp = fr.get("path")
                meta = fr.get("metadata") if isinstance(fr.get("metadata"), dict) else {}
                inp = meta.get("input_path") or meta.get("source_path")
                if (
                    isinstance(outp, str)
                    and outp.strip()
                    and isinstance(inp, str)
                    and inp.strip()
                ):
                    merged = dict(meta)
                    merged.setdefault(
                        "link_kind",
                        "batchfile_metadata_pair",
                    )
                    merged.update(
                        {
                            "endpoint": endpoint,
                            "pipeline_root_job_id": root_job_id,
                            "step_job_id": step_job_id or "",
                            "from_payload": "batchfile_metadata",
                        }
                    )
                    rows.append(
                        {
                            "input_path": inp.strip(),
                            "output_path": outp.strip(),
                            "metadata": merged,
                        }
                    )

    payload = _parse_json_object_from_text_response(response_data)
    if payload:
        pair_rows = payload.get("file_pair_rows")
        if isinstance(pair_rows, list):
            for pr in pair_rows[:_MAX_IO_ROWS_PER_JOB]:
                if not isinstance(pr, dict):
                    continue
                inp = pr.get("input_path")
                outp = pr.get("output_path")
                if not isinstance(inp, str) or not isinstance(outp, str):
                    continue
                if not inp.strip() or not outp.strip():
                    continue
                meta = pr.get("metadata") if isinstance(pr.get("metadata"), dict) else {}
                merged = dict(meta)
                merged.setdefault("link_kind", "file_pair_rows")
                merged.update(
                    {
                        "endpoint": endpoint,
                        "pipeline_root_job_id": root_job_id,
                        "step_job_id": step_job_id or "",
                        "from_payload": "file_pair_rows",
                    }
                )
                rows.append(
                    {
                        "input_path": inp.strip(),
                        "output_path": outp.strip(),
                        "metadata": merged,
                    }
                )

        is_summarize = _is_image_summarize_endpoint(endpoint)
        is_img_payload = bool(payload.get("image_summary"))
        pairs = payload.get("file_pairs")
        if (
            isinstance(pairs, list)
            and pairs
            and not (is_summarize and is_img_payload)
        ):
            for pair in pairs[:_MAX_IO_ROWS_PER_JOB]:
                if not isinstance(pair, dict):
                    continue
                inp = pair.get("input_path")
                outp = pair.get("output_path")
                if not isinstance(inp, str) or not isinstance(outp, str):
                    continue
                if not inp.strip() or not outp.strip():
                    continue
                rows.append(
                    {
                        "input_path": inp.strip(),
                        "output_path": outp.strip(),
                        "metadata": {
                            "link_kind": "file_pairs",
                            "endpoint": endpoint,
                            "pipeline_root_job_id": root_job_id,
                            "step_job_id": step_job_id or "",
                            "from_payload": "file_pairs",
                        },
                    }
                )

    if rows:
        insert_pipeline_io_links(user_id, root_job_id, rows)
        logger.info(
            "Pipeline index: recorded %d generic I/O link(s) for job %s (%s)",
            len(rows),
            root_job_id,
            endpoint,
        )


def record_image_summary_for_pipeline(
    user_id: str,
    root_job_id: str,
    endpoint: str,
    response_data: Any,
) -> None:
    """
    After image_summary/summarize-images completes, store one row per summary .txt
    with its source image path (1:1).
    """
    if not user_id or not root_job_id:
        return
    el = (endpoint or "").lower()
    if "image_summary" not in el or "summarize" not in el:
        return

    raw = _parse_text_response_value(response_data)
    if not raw:
        return
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return
    if not isinstance(payload, dict) or not payload.get("image_summary"):
        return

    input_dir = str(payload.get("input_dir") or "")
    files = payload.get("files") or []
    file_pairs = payload.get("file_pairs")
    if not isinstance(files, list):
        return
    if not input_dir and not file_pairs:
        return

    rows: List[Dict[str, Any]] = []

    if isinstance(file_pairs, list) and file_pairs:
        for pair in file_pairs:
            if not isinstance(pair, dict):
                continue
            fp = pair.get("output_path")
            img = pair.get("input_path")
            if not isinstance(fp, str) or not isinstance(img, str) or not fp.strip():
                continue
            excerpt = ""
            try:
                from pathlib import Path

                excerpt = Path(fp).read_text(encoding="utf-8", errors="replace")[:8000]
            except OSError:
                pass
            rows.append(
                {
                    "text_path": fp,
                    "source_image_path": img,
                    "text_excerpt": excerpt,
                    "provenance": {
                        "endpoint": endpoint,
                        "input_dir": input_dir,
                        "pipeline_root_job_id": root_job_id,
                        "from_payload": "file_pairs",
                    },
                }
            )
    else:
        if not input_dir:
            return
        for fp in files:
            if not isinstance(fp, str) or not fp.strip():
                continue
            img = source_image_path_from_summary(fp, input_dir)
            if not img:
                logger.debug("Could not infer source image for summary file %s", fp)
                continue
            excerpt = ""
            try:
                from pathlib import Path

                excerpt = Path(fp).read_text(encoding="utf-8", errors="replace")[:8000]
            except OSError:
                pass
            rows.append(
                {
                    "text_path": fp,
                    "source_image_path": img,
                    "text_excerpt": excerpt,
                    "provenance": {
                        "endpoint": endpoint,
                        "input_dir": input_dir,
                        "pipeline_root_job_id": root_job_id,
                        "from_payload": "filename_heuristic",
                    },
                }
            )

    if rows:
        insert_chunks(user_id, root_job_id, rows)
        logger.info(
            "Pipeline index: recorded %d image↔text row(s) for job %s",
            len(rows),
            root_job_id,
        )
