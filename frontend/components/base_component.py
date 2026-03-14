"""
Base Component Classes

This module provides base classes and utilities for component development.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from nicegui import ui

# Configure logging for components
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BaseComponent(ABC):
    """
    Base class for UI components.

    Provides common functionality and patterns for component development.
    """

    def __init__(self, **kwargs):
        """
        Initialize the base component.

        Args:
            **kwargs: Component-specific configuration
        """
        self.config = kwargs
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.info(f"Initializing {self.__class__.__name__}")

    @abstractmethod
    def render(self) -> Any:
        """
        Render the component.

        Must be implemented by subclasses to define how the component
        is rendered in the UI.

        Returns:
            Any: The rendered component or container
        """
        pass

    def create_error_display(self, message: str) -> ui.element:
        """
        Create a standardized error display.

        Args:
            message: Error message to display

        Returns:
            ui.element: Error display element
        """
        with ui.card().classes('bg-red-50 border border-red-300 p-4') as error_card:
            ui.label('Error').classes('text-lg font-semibold text-red-700 mb-2')
            ui.label(message).classes('text-red-600')
        return error_card

    def create_loading_display(self, message: str = "Loading...") -> ui.element:
        """
        Create a standardized loading display.

        Args:
            message: Loading message to display

        Returns:
            ui.element: Loading display element
        """
        with ui.row().classes('items-center gap-2') as loading_row:
            ui.spinner(size='sm')
            ui.label(message).classes('text-sm text-gray-600')
        return loading_row

    def create_success_display(self, message: str) -> ui.element:
        """
        Create a standardized success display.

        Args:
            message: Success message to display

        Returns:
            ui.element: Success display element
        """
        with ui.card().classes('bg-green-50 border border-green-300 p-4') as success_card:
            ui.label('Success').classes('text-lg font-semibold text-green-700 mb-2')
            ui.label(message).classes('text-green-600')
        return success_card

    def log_action(self, action: str, details: Optional[str] = None):
        """
        Log a component action.

        Args:
            action: Action being performed
            details: Additional details
        """
        message = f"{self.__class__.__name__}: {action}"
        if details:
            message += f" - {details}"
        self.logger.info(message)


class ComponentRegistry:
    """
    Registry for component instances.

    Provides a centralized way to manage and access component instances.
    """

    _instances: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, instance: Any):
        """
        Register a component instance.

        Args:
            name: Unique name for the component
            instance: Component instance to register
        """
        cls._instances[name] = instance
        logger.info(f"Registered component: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        """
        Get a registered component instance.

        Args:
            name: Name of the component to retrieve

        Returns:
            Optional[Any]: Component instance or None if not found
        """
        return cls._instances.get(name)

    @classmethod
    def unregister(cls, name: str):
        """
        Unregister a component instance.

        Args:
            name: Name of the component to unregister
        """
        if name in cls._instances:
            del cls._instances[name]
            logger.info(f"Unregistered component: {name}")

    @classmethod
    def list_components(cls) -> list:
        """
        List all registered component names.

        Returns:
            list: List of registered component names
        """
        return list(cls._instances.keys())
