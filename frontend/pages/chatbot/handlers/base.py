from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.chat import UIOperations
from frontend.utils.ui import safe_ui_call


class BaseHandler:
    """Base class for all handler classes providing common functionality."""

    def __init__(self, logger_name: str | None = None):
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)


class FormErrorHandler:
    def display_error_boundary(self, container, title: str, message: str):
        UIOperations.safe_notify(f"{title}: {message}", type="negative")

        def _add_label():
            with container:
                ui.label(f"Error: {message}").classes(
                    "p-4 bg-red-50 text-red-700 rounded border border-red-200"
                )

        safe_ui_call(_add_label)
