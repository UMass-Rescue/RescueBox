"""
Error Handler.

Centralized error handling with consistent UI feedback.
"""

import logging
import asyncio
from typing import Optional

from frontend.pages.chatbot.utils.ui_operations import UIOperations

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling with consistent UI feedback."""

    @staticmethod
    async def handle_with_ui_feedback(operation_func, error_message: str,
                                    show_error_callback=None, notify_type='negative'):
        """Execute operation with consistent error handling and UI feedback."""
        try:
            return await operation_func()
        except Exception as e:
            logger.error("%s: %s", error_message, str(e))
            if show_error_callback:
                if asyncio.iscoroutinefunction(show_error_callback):
                    await show_error_callback(f"{error_message}: {str(e)}")
                else:
                    show_error_callback(f"{error_message}: {str(e)}")
            else:
                UIOperations.safe_notify(f"{error_message}: {str(e)}", type=notify_type)
            return None

    @staticmethod
    def handle_sync_with_ui_feedback(operation_func, error_message: str,
                                   show_error_callback=None, notify_type='negative'):
        """Execute synchronous operation with consistent error handling and UI feedback."""
        try:
            return operation_func()
        except Exception as e:
            logger.error("%s: %s", error_message, str(e))
            if show_error_callback:
                if asyncio.iscoroutinefunction(show_error_callback):
                    # For sync context, we can't await - just log
                    logger.warning("Cannot await async show_error_callback in sync context")
                else:
                    show_error_callback(f"{error_message}: {str(e)}")
            else:
                UIOperations.safe_notify(f"{error_message}: {str(e)}", type=notify_type)
            return None
