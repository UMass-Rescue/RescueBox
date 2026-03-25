"""
Logs Page

This module provides the LogsPage class for displaying application log files.
It allows users to view the contents of the RescueBox log file in real-time.
"""

import logging
from pathlib import Path
from nicegui import ui

# Setup backend path for imports
from frontend.utils.path_setup import setup_backend_path
setup_backend_path()

from frontend.components.shared import create_navbar
from frontend.pages.logs.logs_utils import read_log_file, format_log_content, get_log_file_info
from frontend.config import LOG_FILE
from frontend.constants import UI_TITLES, ERROR_MESSAGES

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LogsPage:
    """
    Logs display page.

    Displays the contents of the application log file in a scrollable,
    formatted view. Provides refresh functionality to view latest logs.

    Usage:
        page = LogsPage()
        await page.render()

    Tips:
        - Log file is read on each render for latest content
        - Large log files are truncated to last 1000 lines for performance
        - Uses monospace font for better log readability
        - Auto-scrolls to bottom to show latest entries
    """

    def __init__(self):
        """Initialize the logs page."""
        self.log_content = ""
        self.max_lines = 1000  # Limit lines for performance

    async def render(self):
        """
        Render the logs page.

        Creates the UI components for displaying log content with
        refresh functionality and proper formatting.
        """
        logger.info("Rendering logs page")

        with ui.column().classes('w-full max-w-full min-w-0 p-4 gap-4 flex flex-col flex-1'):
            # Page header
            ui.label(UI_TITLES.get('logs', 'Application Logs')).classes('text-2xl font-bold mb-4')

            # Use extracted log viewer component (full width, fill available space)
            try:
                from frontend.components.logs.log_viewer import render_log_viewer
                log_container = ui.column().classes('w-full max-w-full min-w-0 flex-1')
                self.log_display = render_log_viewer(log_container, LOG_FILE, self.max_lines)
                # Load initial content into returned element if available
                if self.log_display is not None:
                    await self._load_logs()
            except Exception as e:
                # Fallback to inline rendering if component fails
                logger.exception("Failed to use log_viewer component: %s", e)
                with ui.row().classes('gap-4 items-center mb-4'):
                    ui.button('Refresh', on_click=self._refresh_logs).props('icon=refresh').classes('px-4 py-2')
                    log_path = str(LOG_FILE)
                    ui.label(f'Log file: {log_path}').classes('text-sm text-gray-600')

                with ui.card().classes('w-full max-w-full'):
                    with ui.scroll_area().classes('min-h-[calc(100vh-12rem)] w-full'):
                        self.log_display = ui.code().classes('w-full text-xs font-mono whitespace-pre-wrap')
                        self.log_display.props('language=text')
                await self._load_logs()

        logger.info("Logs page rendered successfully")

    async def _load_logs(self):
        """
        Load and display log file contents.

        Reads the log file, limits to max_lines, and displays in the UI.
        Shows error message if log file cannot be read.
        """
        self.log_content = read_log_file(LOG_FILE, self.max_lines)
        formatted_content = format_log_content(self.log_content)

        self.log_display.content = formatted_content

        # Auto-scroll to bottom
        await ui.run_javascript('''
            const scrollArea = document.querySelector('.q-scrollarea__content');
            if (scrollArea) {
                scrollArea.scrollTop = scrollArea.scrollHeight;
            }
        ''', timeout=10)

        logger.debug(f"Loaded log content from: {LOG_FILE}")

    async def _refresh_logs(self):
        """Refresh the log display by reloading content."""
        logger.info("Refreshing logs")
        await self._load_logs()
        ui.notify('Logs refreshed', type='positive')


@ui.page('/logs')
async def logs_page():
    """
    Page route handler for /logs.

    Creates the logs page with navigation bar and renders the LogsPage.

    Returns:
        None: Page is rendered directly
    """
    logger.info("Logs page route accessed")
    from frontend.utils.theme import apply_saved_theme
    apply_saved_theme()
    create_navbar()
    logs_page_instance = LogsPage()
    await logs_page_instance.render()
