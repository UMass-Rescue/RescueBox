"""
UI Operations.

Safe UI operations that work in both normal and test environments.
"""

import logging
import asyncio
from typing import Optional

from nicegui import ui

logger = logging.getLogger(__name__)


class UIOperations:
    """Safe UI operations that work in both normal and test environments."""

    @staticmethod
    async def safe_navigate_to(path: str, delay: float = 0.5):
        """Navigate to path with safe error handling for test environments."""
        try:
            ui.navigate.to(path)
            if delay > 0:
                await asyncio.sleep(delay)
        except RuntimeError as ui_error:
            if "slot cannot be determined" in str(ui_error):
                logger.debug("UI navigation skipped in test environment: %s", ui_error)
            else:
                raise

    @staticmethod
    def safe_notify(message: str, type: str = 'info', timeout: Optional[int] = None):
        """Show notification with safe error handling for test environments."""
        try:
            if timeout:
                ui.notify(message, type=type, timeout=timeout)
            else:
                ui.notify(message, type=type)
        except RuntimeError as ui_error:
            if "slot cannot be determined" in str(ui_error):
                logger.debug("UI notification skipped in test environment: %s", ui_error)
            else:
                raise

    @staticmethod
    async def safe_container_update(container):
        """Update container with safe error handling for test environments."""
        try:
            container.update()
        except RuntimeError as ui_error:
            if "slot cannot be determined" in str(ui_error):
                logger.debug("Container update skipped in test environment: %s", ui_error)
            else:
                raise

    @staticmethod
    def scroll_to_bottom():
        """Scroll the page to the bottom with a slight delay for layout calculation."""
        ui.run_javascript("""
            setTimeout(() => {
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            }, 100);
        """)
