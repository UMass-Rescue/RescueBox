"""
Form Error Handler.

Centralized error display and cleanup logic for form operations.
Eliminates duplication between FormProcessor and JobSubmissionOrchestrator.
"""

import logging
from nicegui import ui

from frontend.pages.chatbot.utils.ui_operations import UIOperations
from frontend.pages.chatbot.utils.ui_styling import UIStyling


logger = logging.getLogger(__name__)


class FormErrorHandler:
    """Handles error display and cleanup for form operations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def display_error_boundary(self, container, title: str, message: str, technical_details: str = None, icon: str = "error"):
        """
        Display a user-friendly error boundary with recovery options.

        Args:
            container: UI container to display error in
            title: Error title (e.g., "Network Error")
            message: User-friendly error message
            technical_details: Technical details for debugging
            icon: Material icon name for the error
        """
        self.logger.info("Displaying error boundary for: %s", title)
        self.logger.info("Container type: %s, Container repr: %s", type(container), repr(container))

        # Also show a notification for immediate feedback
        UIOperations.safe_notify(f"Error: {message}", type="negative", timeout=5000)

        try:
            # Delegate to extracted error boundary component when available
            from frontend.components.errors.error_boundary import render_error_boundary
            render_error_boundary(container, title, message, technical_details=technical_details, icon=icon)
            self.logger.info("Error boundary rendered via component")
            UIOperations.safe_container_update(container)
            UIOperations.scroll_to_bottom()
        except Exception as display_error:
            self.logger.error("Failed to display error boundary component: %s", str(display_error))
            # Fallback: simple inline error display
            try:
                with container:
                    with ui.card().classes(UIStyling.CARD_ERROR_DISPLAY):
                        with ui.row().classes('items-start gap-4'):
                            ui.icon(icon, size='3rem').classes(UIStyling.ICON_ERROR)
                            with ui.column().classes('flex-1'):
                                ui.label(f'🚫 {title}').classes(UIStyling.LABEL_ERROR_DISPLAY_TITLE)
                                ui.label(message).classes(UIStyling.LABEL_ERROR_DISPLAY_MESSAGE)
                                if technical_details:
                                    with ui.expansion('Technical Details').classes(UIStyling.EXPANSION_ERROR_DETAILS):
                                        ui.label(technical_details).classes(UIStyling.LABEL_ERROR_TECHNICAL)
                UIOperations.safe_container_update(container)
            except Exception as fallback_error:
                self.logger.error("Failed to display fallback error: %s", str(fallback_error))

    def clean_error_message(self, raw_error: str) -> str:
        """Clean up error message to make it more user-friendly."""
        # Extract the actual error message from common prefixes
        if "Job submission failed:" in raw_error:
            return raw_error.split("Job submission failed:", 1)[1].strip()
        elif "Exception:" in raw_error:
            return raw_error.split("Exception:", 1)[1].strip()
        return raw_error
