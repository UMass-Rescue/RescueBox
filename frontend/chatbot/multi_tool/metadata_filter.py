"""Metadata criteria parsing and batch-item filtering helpers."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def _parse_age_range_for_comparison(mval_str: str) -> float | None:
    """Parse ``(min-max)`` age bucket strings and return the upper bound."""
    m = re.match(r"\((\d+)-(\d+)\)", mval_str.strip())
    if m:
        return float(m.group(2))
    return 0


def _meta_get(meta: dict[str, Any], key: str) -> Any | None:
    """Case-insensitive metadata field lookup."""
    k = key.strip()
    if k in meta:
        return meta[k]
    kl = k.lower()
    for mk, mv in meta.items():
        if str(mk).lower() == kl:
            return mv
    return None


def _item_matches_all_criteria(meta: dict[str, Any], criteria: list[str]) -> bool:
    for clause in criteria:
        if not _metadata_matches_clause(meta, clause):
            return False
    return True


def _metadata_matches_clause(meta: dict[str, Any], clause: str) -> bool:
    parsed = _parse_metadata_filter_clause(clause)
    if parsed is None:
        return True
    key, val, bare_cmp = parsed
    mval = _meta_get(meta, key)
    if mval is None:
        return False
    return _compare_metadata_to_filter(str(mval), key, val, bare_cmp)


def _parse_metadata_filter_clause(
    clause: str,
) -> tuple[str, str, str | None] | None:
    """Parse one filter clause into (key, value, optional comparison operator)."""
    bare_cmp: str | None = None
    m = re.match(r"^\s*(\S+)\s*(<=|>=|<|>)\s*(.+)\s*$", clause)
    if m:
        key, bare_cmp, val = m.group(1), m.group(2), m.group(3)
    elif ":" in clause:
        key, val = clause.split(":", 1)
    elif "=" in clause:
        key, val = clause.split("=", 1)
    else:
        return None
    return key.strip(), val.strip(), bare_cmp


def _compare_metadata_to_filter(
    mval_str: str,
    key: str,
    val: str,
    bare_cmp: str | None,
) -> bool:
    key_lower = key.lower()
    age_num = _parse_age_range_for_comparison(mval_str) if key_lower == "age" else None
    if bare_cmp is not None:
        return _compare_with_bare_operator(mval_str, key_lower, val, bare_cmp)
    if val.startswith(">"):
        return _compare_prefix_operator(mval_str, val, ">", age_num)
    if val.startswith("<"):
        return _compare_prefix_operator(mval_str, val, "<", age_num)
    return _compare_equality(mval_str, key_lower, val, age_num)


def _compare_with_bare_operator(
    mval_str: str,
    key_lower: str,
    val: str,
    bare_cmp: str,
) -> bool:
    try:
        cmp_val = float(val)
    except (ValueError, TypeError):
        return False
    if key_lower == "age":
        an = _parse_age_range_for_comparison(mval_str)
        if bare_cmp == "<":
            return an < cmp_val
        if bare_cmp == ">":
            return an > cmp_val
        if bare_cmp == "<=":
            return an <= cmp_val
        return an >= cmp_val
    try:
        n = float(mval_str)
    except (ValueError, TypeError):
        return False
    if bare_cmp == "<":
        return n < cmp_val
    if bare_cmp == ">":
        return n > cmp_val
    if bare_cmp == "<=":
        return n <= cmp_val
    return n >= cmp_val


def _compare_prefix_operator(
    mval_str: str, val: str, op: str, age_num: float | None
) -> bool:
    try:
        cmp_val = float(val[1:].strip())
        if age_num is not None:
            return age_num > cmp_val if op == ">" else age_num < cmp_val
        n = float(mval_str)
        return n > cmp_val if op == ">" else n < cmp_val
    except (ValueError, TypeError):
        return mval_str == val[1:].strip()


def _compare_equality(
    mval_str: str, key_lower: str, val: str, age_num: float | None
) -> bool:
    if age_num is not None:
        try:
            return age_num == float(val)
        except (ValueError, TypeError):
            return mval_str == val
    if key_lower == "gender":
        return mval_str.strip().lower() == val.strip().lower()
    return mval_str == val


def apply_metadata_filter(items: list[dict[str, Any]], criteria_str: str) -> list[str]:
    """Filter batch rows by metadata criteria and return matching paths."""
    if not criteria_str or not criteria_str.strip():
        paths = [it["path"] for it in items]
        logger.debug(
            "apply_metadata_filter: empty criteria - passing all %d file(s): %s",
            len(paths),
            paths,
        )
        return paths
    criteria = [c.strip() for c in criteria_str.split(",") if c.strip()]
    if not criteria:
        paths = [it["path"] for it in items]
        logger.debug(
            "apply_metadata_filter: no parseable criteria tokens - passing all %d file(s): %s",
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
        match = _item_matches_all_criteria(meta, criteria)
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
        "apply_metadata_filter: done - %d matched path(s) of %d: %s",
        len(result),
        len(items),
        result,
    )
    return result
