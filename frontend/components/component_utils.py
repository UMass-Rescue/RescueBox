"""
Component Utilities

This module provides shared utilities and helper functions for components.
"""

import logging
from datetime import datetime
from typing import Any

from nicegui import ui

from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def setup_component_imports():
    """
    Setup common imports needed by components.

    This function ensures backend models are available to components.
    """


def format_timestamp(timestamp: str, format_type: str = "relative") -> str:
    """
    Format a timestamp for display.

    Args:
        timestamp: ISO format timestamp string
        format_type: Type of formatting ('relative', 'absolute', 'short')

    Returns:
        str: Formatted timestamp
    """
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            dt = timestamp

        if format_type == "relative":
            now = datetime.now()
            diff = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt

            if not diff.days:
                if diff.seconds < 60:
                    return "Just now"
                if diff.seconds < 3600:
                    return f"{diff.seconds // 60} minutes ago"
                return f"{diff.seconds // 3600} hours ago"
            if diff.days == 1:
                return "Yesterday"
            if diff.days < 7:
                return f"{diff.days} days ago"
            return dt.strftime("%Y-%m-%d")

        if format_type == "absolute":
            return dt.strftime("%Y-%m-%d %H:%M:%S")

        if format_type == "short":
            return dt.strftime("%m/%d %H:%M")

        return str(dt)

    except UI_RENDER_ERRORS as e:
        logger.warning("Error formatting timestamp %s: %s", timestamp, e)
        return str(timestamp)


def create_card_container(title: str = None, classes: str = "") -> Any:
    """
    Create a standardized card container.

    Args:
        title: Optional title for the card
        classes: Additional CSS classes

    Returns:
        Card container context manager
    """
    base_classes = "bg-white border border-zinc-200 rounded-lg shadow-sm"
    if classes:
        base_classes += f" {classes}"

    card = ui.card().classes(base_classes)

    if title:
        ui.label(title).classes("text-lg font-semibold mb-4")

    return card


def validate_component_config(config: dict[str, Any], required_keys: list) -> bool:
    """
    Validate component configuration.

    Args:
        config: Configuration dictionary
        required_keys: List of required configuration keys

    Returns:
        bool: True if configuration is valid
    """
    for key in required_keys:
        if key not in config:
            logger.error("Missing required configuration key: %s", key)
            return False

        if config[key] is None:
            logger.error("Configuration key %s cannot be None", key)
            return False

    return True


def get_component_theme_colors(component_type: str) -> dict[str, str]:
    """
    Get theme colors for a component type.

    Args:
        component_type: Type of component (e.g., 'success', 'error', 'info')

    Returns:
        Dict[str, str]: Color configuration
    """
    themes = {
        "success": {
            "bg": "bg-green-50",
            "border": "border-green-300",
            "text": "text-green-700",
            "icon": "text-green-600",
        },
        "error": {
            "bg": "bg-red-50",
            "border": "border-red-300",
            "text": "text-red-700",
            "icon": "text-red-600",
        },
        "warning": {
            "bg": "bg-yellow-50",
            "border": "border-yellow-300",
            "text": "text-yellow-700",
            "icon": "text-yellow-600",
        },
        "info": {
            "bg": "bg-zinc-50",
            "border": "border-zinc-300",
            "text": "text-zinc-700",
            "icon": "text-zinc-600",
        },
    }

    return themes.get(component_type, themes["info"])


def log_component_event(
    component_name: str, event: str, details: dict[str, Any] | None = None
):
    """
    Log a component event with structured information.

    Args:
        component_name: Name of the component
        event: Event that occurred
        details: Additional event details
    """
    message = f"{component_name}: {event}"
    if details:
        message += f" - {details}"

    logger.info(message)


def create_success_card_element(message: str) -> ui.element:
    """Standard green success card (shared by layout and base components)."""
    with ui.card().classes("bg-green-50 border border-green-300 p-4") as success_card:
        ui.label("Success").classes("text-lg font-semibold text-green-700 mb-2")
        ui.label(message).classes("text-green-600")
    return success_card
