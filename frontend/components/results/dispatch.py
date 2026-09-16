"""Dispatch plugin response bodies to type-specific renderers."""

from __future__ import annotations

import json
import logging
from typing import Any

from rb.api import models as rb_api_models

from frontend.components.ui_exceptions import UI_RENDER_ERRORS

from .directory import (
    render_batch_directory,
    render_directory,
)
from .file import render_batch_file, render_file
from .text import (
    render_batch_text,
    render_markdown,
    render_text,
)

logger = logging.getLogger(__name__)

_RENDERERS = {
    "file": render_file,
    "directory": render_directory,
    "batchfile": render_batch_file,
    "text": render_text,
    "markdown": render_markdown,
    "batchtext": render_batch_text,
    "batchdirectory": render_batch_directory,
}

_MODEL_BY_OUTPUT_TYPE = {
    "file": rb_api_models.FileResponse,
    "directory": rb_api_models.DirectoryResponse,
    "batchfile": rb_api_models.BatchFileResponse,
    "text": rb_api_models.TextResponse,
    "markdown": rb_api_models.MarkdownResponse,
    "batchtext": rb_api_models.BatchTextResponse,
    "batchdirectory": rb_api_models.BatchDirectoryResponse,
}


class ResultDispatcher:
    def __init__(self):
        self._renderers = None

    def register_renderer(self, output_type: str, renderer) -> None:
        """Register or override a renderer for an output type."""
        self.renderers[output_type] = renderer

    @property
    def renderers(self):
        if self._renderers is None:
            self._renderers = dict(_RENDERERS)
        return self._renderers

    def render(self, container, root):
        try:
            otype = root.get("output_type")
            renderer = self.renderers.get(otype)
            if not renderer:
                return
            try:
                cls = _MODEL_BY_OUTPUT_TYPE.get(otype)
                renderer(container, cls(**root) if cls else root)
            except UI_RENDER_ERRORS:
                renderer(container, root)
        except UI_RENDER_ERRORS as e:
            logger.error("Dispatch error: %s", e)


dispatcher = ResultDispatcher()


class ResultsPreview:
    @staticmethod
    def supported_output_types():
        """Output type keys handled by the dispatcher."""
        return list(_RENDERERS.keys())

    @staticmethod
    def render(container, response):
        try:
            dispatcher.render(
                container,
                response.model_dump() if hasattr(response, "model_dump") else response,
            )
        except UI_RENDER_ERRORS as e:
            logger.error("Preview render failed: %s", e)


def augment_response_model_dump_for_image_summary(
    dump: dict[str, Any], job_fields: dict[str, Any]
) -> dict[str, Any]:
    """Inject image-summary metadata into response dump for thumbnail rendering."""
    try:
        root = dump.get("root")
        if not root or not isinstance(root, dict):
            return dump
        val = root.get("value")
        if not val or not isinstance(val, str):
            return dump
        try:
            data = json.loads(val)
            if isinstance(data, dict) and data.get("image_summary"):
                data["input_dir"] = (
                    job_fields.get("request", {})
                    .get("inputs", {})
                    .get("input_dir", {})
                    .get("path", "")
                )
                root["value"] = json.dumps(data)
        except (json.JSONDecodeError, TypeError):
            pass
    except UI_RENDER_ERRORS as e:
        logger.error("Augmentation error: %s", e)
    return dump
