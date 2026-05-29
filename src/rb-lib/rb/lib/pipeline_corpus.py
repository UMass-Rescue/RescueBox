"""
Shared helpers for pipeline vs standalone file corpora.

Plugins that accept an optional ``file_filter`` (``BatchFileInput``) merged at HTTP
layer should use :func:`resolve_text_file_corpus_paths` so that:

* When ``file_filter`` is **absent**, they scan a directory (standalone use).
* When ``file_filter`` is **present**, they use **only** listed paths and never
  fall back to listing the directory (avoids stale siblings after summarize, etc.).
"""

from __future__ import annotations

import os
from typing import Any, FrozenSet, Optional

_DEFAULT_TEXT_EXTENSIONS: FrozenSet[str] = frozenset({".txt", ".text", ".md", ".log"})


def list_text_files_in_directory(
    input_dir: str,
    *,
    allowed_extensions: Optional[FrozenSet[str]] = None,
) -> list[str]:
    """Return sorted list of text file paths directly under ``input_dir`` (non-recursive)."""
    exts = allowed_extensions if allowed_extensions is not None else _DEFAULT_TEXT_EXTENSIONS
    paths: list[str] = []
    try:
        names = sorted(os.listdir(input_dir))
    except OSError:
        return []
    for name in names:
        path = os.path.join(input_dir, name)
        if os.path.isfile(path) and os.path.splitext(path)[1].lower() in exts:
            paths.append(path)
    return paths


def get_file_filter_from_inputs(inputs: Any) -> Any:
    """Return ``file_filter`` if present on dict-like or object inputs, else ``None``."""
    if isinstance(inputs, dict):
        return inputs.get("file_filter")
    return getattr(inputs, "file_filter", None)


def resolve_text_file_corpus_paths(
    inputs: Any,
    input_dir: str,
    *,
    allowed_extensions: Optional[FrozenSet[str]] = None,
    empty_dir_error: str = "No text files found in directory",
) -> tuple[list[str], str]:
    """
    Resolve which text files a tool should process for this request.

    If ``file_filter`` is missing, list text files under ``input_dir``.

    If ``file_filter`` is present (pipeline), use only paths in ``file_filter.files``
    that exist as files — **never** scan ``input_dir``.

    Returns ``(paths, error_message)``. ``error_message`` is empty iff ``paths`` is non-empty.
    """
    ff = get_file_filter_from_inputs(inputs)
    if ff is None:
        paths = list_text_files_in_directory(input_dir, allowed_extensions=allowed_extensions)
        if not paths:
            return [], empty_dir_error
        return paths, ""

    files = getattr(ff, "files", None)
    if files is None and isinstance(ff, dict):
        files = ff.get("files")
    files = list(files or [])
    if not files:
        return [], "file_filter is empty; not scanning directory"

    paths: list[str] = []
    for f in files:
        p = f.get("path") if isinstance(f, dict) else getattr(f, "path", None)
        if p is None:
            continue
        ps = str(p) if not isinstance(p, str) else p
        if os.path.isfile(ps):
            paths.append(ps)
    if not paths:
        return [], "No file paths from file_filter exist on disk"
    return paths, ""
