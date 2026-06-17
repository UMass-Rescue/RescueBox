from __future__ import annotations

import logging
from typing import Optional

from nicegui import ui

from frontend.components.chat import UIOperations
from frontend.utils.ui import _safe_ui_call


class BaseHandler:
    """Base class for all handler classes providing common functionality."""

    def __init__(self, logger_name: Optional[str] = None):
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)

    def log_debug(self, message: str, *args) -> None:
        """Log at debug level using the handler logger."""
        self.logger.debug(message, *args)

    def log_warning(self, message: str, *args) -> None:
        """Log at warning level using the handler logger."""
        self.logger.warning(message, *args)


class FormErrorHandler:
    def display_error_boundary(self, container, title: str, message: str):
        UIOperations.safe_notify(f"{title}: {message}", type="negative")

        def _add_label():
            with container:
                ui.label(f"Error: {message}").classes(
                    "p-4 bg-red-50 text-red-700 rounded border border-red-200"
                )

        _safe_ui_call(_add_label)

    def notify_form_error(self, title: str, message: str) -> None:
        """Surface a form error without requiring a container."""
        UIOperations.safe_notify(f"{title}: {message}", type="negative")
