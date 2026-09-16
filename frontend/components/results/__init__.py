"""Job result renderers by response type (file, directory, text, batch, …).

``os``, ``platform``, ``subprocess``, and ``ui`` are re-exported so unit tests can
patch ``frontend.components.results.<name>`` (see frontend/readme.md).
"""

import os  # noqa: F401 — patch target for unit tests
import platform  # noqa: F401
import subprocess  # noqa: F401

from nicegui import ui  # noqa: F401

from . import (  # noqa: F401
    image_summary,
    table_helpers,
)
from . import (
    serve_paths as _serve_paths_module,
)
from .directory import render_batch_directory, render_directory
from .dispatch import (
    ResultsPreview,
    augment_response_model_dump_for_image_summary,
    dispatcher,
)
from .file import render_batch_file, render_file
from .serve_paths import open_file, open_folder
from .table_helpers import (
    create_bbox_preview_row_click_handler,
    create_directory_row_click_handler,
    create_file_row_click_handler,
    create_metadata_table_columns,
    create_sortable_table,
    parse_int_bbox,
    resolve_row_idx,
    resolve_table_row_index,
)
from .text import (
    open_text_markdown_modal,
    render_batch_text,
    render_markdown,
    render_text,
    render_text_search_json,
)
from .tool_selection import (
    clear_active_tool_selection_cards,
    render_tool_selection_message,
)

# Monolithic-module compat for unit tests (patch ``frontend.components.results.*``).
_SERVED_FILES = _serve_paths_module._SERVED_FILES  # pylint: disable=protected-access

__all__ = [
    "ResultsPreview",
    "augment_response_model_dump_for_image_summary",
    "clear_active_tool_selection_cards",
    "create_bbox_preview_row_click_handler",
    "create_directory_row_click_handler",
    "create_file_row_click_handler",
    "create_metadata_table_columns",
    "create_sortable_table",
    "dispatcher",
    "open_file",
    "open_folder",
    "open_text_markdown_modal",
    "parse_int_bbox",
    "render_batch_directory",
    "render_batch_file",
    "render_batch_text",
    "render_directory",
    "render_file",
    "render_markdown",
    "render_text",
    "render_text_search_json",
    "render_tool_selection_message",
    "resolve_row_idx",
    "resolve_table_row_index",
]
