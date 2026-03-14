"""
Results Renderers

This module provides individual renderer functions for different response types.
It acts as a facade that imports and re-exports renderers from specialized modules
for backward compatibility.

Each renderer handles a specific response type (file, directory, text, etc.)
and creates appropriate UI components.
"""

# Import all renderers from specialized modules
from frontend.components.results.file_renderers import (
    render_file,
    render_batch_file,
)

from frontend.components.results.directory_renderers import (
    render_directory,
    render_batch_directory,
)

from frontend.components.results.renderers import (
    render_text,
    render_markdown,
    render_batch_text,
)

# Re-export for backward compatibility
__all__ = [
    'render_file',
    'render_directory',
    'render_batch_file',
    'render_text',
    'render_markdown',
    'render_batch_text',
    'render_batch_directory',
]
