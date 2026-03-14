"""
Central dispatcher for result renderers.

Provides a simple mapping from response output_type to renderer functions
implemented in `results_renderers`.
"""
import logging
from typing import Any, Dict
from nicegui import ui

logger = logging.getLogger(__name__)

# Lazy import to avoid circular imports at module import time
def _import_renderers():
    from frontend.components.results.results_renderers import (
        render_file,
        render_directory,
        render_batch_file,
        render_text,
        render_markdown,
        render_batch_text,
        render_batch_directory,
    )
    return {
        'file': render_file,
        'directory': render_directory,
        'batchfile': render_batch_file,
        'text': render_text,
        'markdown': render_markdown,
        'batchtext': render_batch_text,
        'batchdirectory': render_batch_directory,
    }


class ResultDispatcher:
    def __init__(self):
        self._renderers = None

    @property
    def renderers(self):
        if self._renderers is None:
            self._renderers = _import_renderers()
        return self._renderers

    def render(self, container: ui.element, root: Dict[str, Any]) -> None:
        """
        Dispatch rendering based on root['output_type'].
        `root` is expected to be a dictionary-like object with an 'output_type' key.
        """
        try:
            output_type = root.get('output_type')
            if not output_type:
                raise ValueError("Missing output_type in result root")
            renderer = self.renderers.get(output_type)
            if not renderer:
                ui.label(f'Unsupported result type: {output_type}').classes('text-red-600')
                logger.error("No renderer for output_type=%s", output_type)
                return
            # Try to instantiate Pydantic model for renderer when possible so renderers
            # can access attributes (path, files, etc.) rather than dict keys.
            try:
                from rb.api import models as rb_models
                model_cls = {
                    'file': rb_models.FileResponse,
                    'directory': rb_models.DirectoryResponse,
                    'batchfile': rb_models.BatchFileResponse,
                    'text': rb_models.TextResponse,
                    'markdown': rb_models.MarkdownResponse,
                    'batchtext': rb_models.BatchTextResponse,
                    'batchdirectory': rb_models.BatchDirectoryResponse,
                }.get(output_type)
                if model_cls:
                    model_instance = model_cls(**root)
                    renderer(container, model_instance)
                else:
                    renderer(container, root)
            except Exception:
                # If model construction fails, fallback to passing dict to renderer
                logger.debug("Could not build model instance for output_type=%s; passing raw dict", output_type)
                renderer(container, root)
        except Exception as e:
            logger.exception("Failed to render result via dispatcher: %s", e)
            ui.label(f'Error rendering result: {e}').classes('text-red-600')


dispatcher = ResultDispatcher()

