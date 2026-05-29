"""
Base Page Class

This module provides a base class for all pages in the application,
offering common functionality and patterns.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Any
from nicegui import ui

from frontend.components.shared import create_navbar
from frontend.utils.error_handling import handle_api_error, show_error_to_user

# Configure logging for base page
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BasePage(ABC):
    """
    Base class for all application pages.

    Provides common functionality for page initialization, rendering,
    and error handling.
    """

    def __init__(self, title: str = "", navbar: bool = True):
        """
        Initialize the base page.

        Args:
            title: Page title for display
            navbar: Whether to include the navigation bar
        """
        self.title = title
        self.include_navbar = navbar
        self.api_client = None  # To be set by subclasses if needed
        logger.info(f"Initializing {self.__class__.__name__}")

    @abstractmethod
    async def render(self) -> None:
        """
        Render the page content.

        Must be implemented by subclasses.
        """
        pass

    def setup_page_layout(self) -> None:
        """
        Setup common page layout elements.

        This includes navigation bar and basic page structure.
        """
        if self.include_navbar:
            create_navbar()

        # Add page title if provided
        if self.title:
            ui.label(self.title).classes('text-2xl font-bold mb-4')

    async def handle_error(self, error: Exception, context: str = "") -> None:
        """
        Handle and display errors in a consistent way.

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        logger.error(error_msg)

        if self.api_client:
            handle_api_error(error, context)
        else:
            show_error_to_user(error_msg)

    def create_loading_indicator(self, message: str = "Loading...") -> ui.element:
        """
        Create a loading indicator element.

        Args:
            message: Loading message to display

        Returns:
            ui.element: The loading indicator element
        """
        try:
            from frontend.components.shared.notifications import render_loading_row
            return render_loading_row(message)
        except Exception:
            with ui.row().classes('items-center gap-2') as loading_row:
                ui.spinner(size='sm')
                ui.label(message).classes('text-sm text-zinc-600')
            return loading_row

    def create_error_card(self, message: str) -> ui.element:
        """
        Create an error card for displaying error messages.

        Args:
            message: Error message to display

        Returns:
            ui.element: The error card element
        """
        try:
            from frontend.components.shared.notifications import render_error_card
            return render_error_card(ui.column(), message)
        except Exception:
            with ui.card().classes('bg-red-50 border border-red-300 p-4') as error_card:
                ui.label('Error').classes('text-lg font-semibold text-red-700 mb-2')
                ui.label(message).classes('text-red-600')
            return error_card

    def create_success_card(self, message: str) -> ui.element:
        """
        Create a success card for displaying success messages.

        Args:
            message: Success message to display

        Returns:
            ui.element: The success card element
        """
        try:
            from frontend.components.shared.notifications import render_success_card
            return render_success_card(ui.column(), message)
        except Exception:
            with ui.card().classes('bg-green-50 border border-green-300 p-4') as success_card:
                ui.label('Success').classes('text-lg font-semibold text-green-700 mb-2')
                ui.label(message).classes('text-green-600')
            return success_card
