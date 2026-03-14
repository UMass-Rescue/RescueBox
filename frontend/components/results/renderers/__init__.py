"""
Result Renderers Package

This package contains specialized renderers for different types of results.
"""

from frontend.components.results.renderers.text_renderer import render_text
from frontend.components.results.renderers.markdown_renderer import render_markdown
from frontend.components.results.renderers.batch_text_renderer import render_batch_text

__all__ = [
    'render_text',
    'render_markdown',
    'render_batch_text',
]
