"""
Logs Page

This module provides the LogsPage class for displaying application log files.
It allows users to view the contents of the RescueBox log file in real-time.
"""

import logging
from pathlib import Path

from nicegui import ui

from frontend.components.logs import read_log_file, render_log_viewer
from frontend.components.shared import create_navbar
from frontend.config import LOG_FILE
from frontend.constants import UI_TITLES
from frontend.utils import apply_saved_theme, require_demo_user_session
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LogsPage:
    """Logs display page. Displays the contents of the application log file in a scrollable,"""

    def __init__(self):
        """Initialize the logs page."""
        self.log_content = ""
        self.max_lines = 1000  # Limit lines for performance
        self.log_display = None

    async def render(self):
        """Render the logs page. Creates the UI components for displaying log content with"""
        logger.info("Rendering logs page")

        with ui.column().classes(
            "container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16 gap-4 flex flex-col flex-1"
        ):
            # Page header
            with ui.row().classes("items-center gap-2 mb-4"):
                ui.label(UI_TITLES.get("logs", "Application Logs")).classes(
                    "text-4xl font-bold text-slate-800"
                )

            # Use extracted log viewer component (full width, fill available space)
            try:
                log_container = ui.column().classes("w-full max-w-full min-w-0 flex-1")
                self.log_display = render_log_viewer(
                    log_container, LOG_FILE, self.max_lines
                )
                # Load initial content into returned element if available
                if self.log_display is not None:
                    await self._load_logs()
            except UI_RENDER_ERRORS as e:
                # Fallback to inline rendering if component fails
                logger.exception("Failed to use log_viewer component: %s", e)

        logger.info("Logs page rendered successfully")

    async def _load_logs(self):
        """Load and display log file contents. Reads the log file, limits to max_lines, and displays in the UI."""
        self.log_content = read_log_file(LOG_FILE, self.max_lines)

        # Cache raw content in log_display and apply search filter if available
        if hasattr(self, "log_display") and self.log_display is not None:
            self.log_display.raw_content = self.log_content
            if hasattr(self.log_display, "apply_filter"):
                self.log_display.apply_filter()
            else:
                formatted_content = format_log_content(self.log_content)
                self.log_display.content = formatted_content
        else:
            formatted_content = format_log_content(self.log_content)
            if hasattr(self, "log_display") and self.log_display is not None:
                self.log_display.content = formatted_content

        # Auto-scroll to bottom
        await ui.run_javascript(
            """
            const scrollArea = document.querySelector('.q-scrollarea__content');
            if (scrollArea) {
                scrollArea.scrollTop = scrollArea.scrollHeight;
            }
        """,
            timeout=10,
        )

        logger.debug("Loaded log content from: %s", LOG_FILE)

    async def refresh_logs(self):
        """Refresh the log display by reloading content."""
        logger.info("Refreshing logs")
        await self._load_logs()
        ui.notify("Logs refreshed", type="positive", classes="rb-notify-505759")


@ui.page("/logs")
async def logs_page():
    """Page route handler for /logs. Creates the logs page with navigation bar and renders the LogsPage."""
    logger.info("Logs page route accessed")
    apply_saved_theme()
    create_navbar()
    if not require_demo_user_session():
        return
    logs_page_instance = LogsPage()
    await logs_page_instance.render()


def format_log_content(content: str) -> str:
    """Format log content for display. Args:"""
    # Basic formatting - could be enhanced with syntax highlighting
    return content.strip()


def get_log_file_info(log_file_path: Path) -> dict:
    """Get information about the log file. Args:"""
    info = {
        "path": str(log_file_path),
        "exists": log_file_path.exists(),
        "size": 0,
        "modified": None,
    }

    if log_file_path.exists():
        stat = log_file_path.stat()
        info["size"] = stat.st_size
        info["modified"] = stat.st_mtime

    return info
