"""
Results Preview Components

This module provides the ResultsPreview class for displaying job results
in various formats. It supports file, directory, text, markdown, and batch
response types with appropriate rendering for each.

The main ResultsPreview class acts as a dispatcher, routing to specialized
renderers in the results_renderers module.
"""

import logging
from nicegui import ui
from typing import Dict, Union, TYPE_CHECKING

if TYPE_CHECKING:
    # Import for type hints only to avoid circular imports
    from rb.api.models import ResponseBody
from pathlib import Path

# Backend models are imported lazily to avoid import order issues
# Import renderers from separate module
from frontend.components.results.results_renderers import (
    render_file,
    render_directory,
    render_batch_file,
    render_text,
    render_markdown,
    render_batch_text,
    render_batch_directory,
)

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ResultsPreview:
    """
    Preview different types of results using Pydantic models.
    
    This class provides static methods for rendering various response types
    from the RescueBox API. It automatically detects the response type and
    renders it appropriately with UI components.
    
    Supported response types:
    - FileResponse: Single file result with preview/opening options
    - DirectoryResponse: Directory result with file listing
    - BatchFileResponse: Multiple files with grouped display
    - TextResponse: Plain text result
    - MarkdownResponse: Markdown formatted text
    - BatchTextResponse: Multiple text items
    - BatchDirectoryResponse: Multiple directories
    
    Usage:
        ResultsPreview.render(container, response_body)
    
    Tips:
    - Response can be a ResponseBody model or dictionary
    - Each response type has specialized rendering logic
    - Images are displayed inline, other files have open buttons
    - Batch responses show first N items with expansion/collapse
    """
    
    @staticmethod
    def render(container, response):
        """
        Render results preview based on response type.

        This static method automatically detects the response type and dispatches
        to the appropriate rendering method. It handles both Pydantic models and
        dictionaries.

        Args:
            container: NiceGUI container element to add the preview to
            response: ResponseBody Pydantic model or dictionary.
                If dict, it will be converted to ResponseBody

        Returns:
            None: Preview is added directly to the container

        Examples:
            >>> ResultsPreview.render(container, response_body)
            >>> ResultsPreview.render(container, {'root': {'output_type': 'text', 'value': 'Result'}})

        Tips:
            - Invalid response format shows an error message
            - Unknown response types show a type name error
            - Each response type has optimized rendering logic
        """
        # Lazy import of backend models to avoid import order issues
        from rb.api.models import (
            ResponseBody,
            FileResponse,
            DirectoryResponse,
            BatchFileResponse,
            TextResponse,
            MarkdownResponse,
            BatchTextResponse,
            BatchDirectoryResponse,
        )

        logger.info("Rendering results preview")
        logger.debug("Response type: %s", type(response).__name__)
        
        # Convert dict to ResponseBody if needed
        if isinstance(response, dict):
            logger.debug("Converting dictionary response to ResponseBody")
            try:
                response_body = ResponseBody(**response)
            except Exception as e:
                logger.error("Invalid response format: %s", str(e))
                ui.label(f'Invalid response format: {str(e)}').classes('text-red-600')
                return
        else:
            response_body = response
        
        # Extract the root union type
        root = response_body.root
        root_type = type(root).__name__
        logger.debug("Response root type: %s", root_type)
        
        # Dispatch using centralized dispatcher
        try:
            from frontend.components.results.dispatcher import dispatcher
            try:
                root_dict = root.model_dump() if hasattr(root, 'model_dump') else (root.dict() if hasattr(root, 'dict') else root)
            except Exception:
                root_dict = root
            dispatcher.render(container, root_dict)
        except Exception as e:
            logger.exception("Dispatcher rendering failed: %s", e)
            ui.label(f'Error rendering result: {e}').classes('text-red-600')
        
        logger.info("Results preview rendered successfully")