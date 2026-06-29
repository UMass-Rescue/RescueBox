"""
Shared structures for plugin inputs/outputs.

Use these TypedDicts in plugin code and in JSON payloads so clients (UI, pipelines)
can pair source files to produced artifacts without inferring from filenames.

See ``frontend/docs/ui-flow.md`` (repo root) for current end-to-end frontend flow.
"""

from __future__ import annotations

from typing import TypeAlias, TypedDict


class InputOutputFilePair(TypedDict):
    """
    Absolute (or normalized) paths: one source file and the output file produced from it.

    Plugins that emit one artifact per input should return a list of these pairs
    (e.g. as ``file_pairs`` in a JSON text response) alongside any flat ``files`` list.
    """

    input_path: str
    output_path: str


# Alias for the image-summary plugin and any code/docs that refer to this name.
ImageSummaryFilePair: TypeAlias = InputOutputFilePair
