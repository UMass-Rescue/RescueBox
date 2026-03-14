"""
Base Handler.

Common base class providing shared logging and error handling functionality
for all handler classes in the chatbot system.
"""

import logging
from abc import ABC
from typing import Optional

from frontend.pages.chatbot.utils.error_handler import ErrorHandler


class BaseHandler(ABC):
    """Base class for all handler classes providing common functionality."""

    def __init__(self, logger_name: Optional[str] = None):
        """
        Initialize the base handler.

        Args:
            logger_name: Name for the logger. If None, uses the class name.
        """
        if logger_name is None:
            logger_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)

    async def handle_error_with_ui_feedback(self, operation_func, error_message: str,
                                          show_error_callback=None, notify_type='negative'):
        """
        Execute operation with consistent error handling and UI feedback.

        Args:
            operation_func: Async function to execute
            error_message: Error message prefix
            show_error_callback: Optional callback to show error in UI
            notify_type: Type of notification to show

        Returns:
            Result of operation_func or None if failed
        """
        return await ErrorHandler.handle_with_ui_feedback(
            operation_func, error_message, show_error_callback, notify_type
        )

    def handle_sync_error_with_ui_feedback(self, operation_func, error_message: str,
                                         show_error_callback=None, notify_type='negative'):
        """
        Execute synchronous operation with consistent error handling and UI feedback.

        Args:
            operation_func: Function to execute
            error_message: Error message prefix
            show_error_callback: Optional callback to show error in UI
            notify_type: Type of notification to show

        Returns:
            Result of operation_func or None if failed
        """
        return ErrorHandler.handle_sync_with_ui_feedback(
            operation_func, error_message, show_error_callback, notify_type
        )
