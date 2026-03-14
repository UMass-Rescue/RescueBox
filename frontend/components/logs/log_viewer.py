import logging
from nicegui import ui
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_log_viewer(container: ui.element, log_file: Path, max_lines: int = 1000):
    """
    Render a log viewer inside `container`. Returns the code element for updates.
    """
    try:
        with container:
            # Controls row
            with ui.row().classes('gap-4 items-center mb-4'):
                refresh_btn = ui.button('Refresh').props('icon=refresh').classes('px-4 py-2')
                ui.label(f'Log file: {str(log_file)}').classes('text-sm text-gray-600')

            # Log content display
            with ui.card().classes('w-full'):
                with ui.scroll_area().classes('h-96 w-full'):
                    log_display = ui.code().classes('w-full text-xs font-mono whitespace-pre-wrap')
                    log_display.props('language=text')

            # Attach simple refresh handler (caller may override or call _load_logs directly)
            def _refresh():
                try:
                    from frontend.pages.logs.logs_utils import read_log_file, format_log_content
                    content = read_log_file(log_file, max_lines)
                    formatted = format_log_content(content)
                    log_display.content = formatted
                except Exception as e:
                    logger.exception("Failed refreshing logs: %s", e)

            refresh_btn.on('click', lambda e=None: _refresh())
            # Return the element for callers to update
            return log_display
    except Exception as e:
        logger.exception("Failed to render log viewer: %s", e)
        with container:
            ui.label(f'Error rendering log viewer: {e}').classes('text-red-600')
        return None

