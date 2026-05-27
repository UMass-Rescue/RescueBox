"""
Component Utilities

This module provides shared utilities and helper functions for components.
"""

import logging
from pathlib import Path
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging for component utilities
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def setup_component_imports():
    """
    Setup common imports needed by components.

    This function ensures backend models are available to components.
    """
    # Add backend models to path if not already there
    backend_path = Path(__file__).parent.parent / 'src'
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))


def format_timestamp(timestamp: str, format_type: str = 'relative') -> str:
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
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp

        if format_type == 'relative':
            now = datetime.now()
            diff = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt

            if diff.days == 0:
                if diff.seconds < 60:
                    return "Just now"
                elif diff.seconds < 3600:
                    return f"{diff.seconds // 60} minutes ago"
                else:
                    return f"{diff.seconds // 3600} hours ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return dt.strftime('%Y-%m-%d')

        elif format_type == 'absolute':
            return dt.strftime('%Y-%m-%d %H:%M:%S')

        elif format_type == 'short':
            return dt.strftime('%m/%d %H:%M')

        else:
            return str(dt)

    except Exception as e:
        logger.warning(f"Error formatting timestamp {timestamp}: {e}")
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
    from nicegui import ui

    base_classes = 'bg-white border border-zinc-200 rounded-lg shadow-sm'
    if classes:
        base_classes += f' {classes}'

    card = ui.card().classes(base_classes)

    if title:
        ui.label(title).classes('text-lg font-semibold mb-4')

    return card


def validate_component_config(config: Dict[str, Any], required_keys: list) -> bool:
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
            logger.error(f"Missing required configuration key: {key}")
            return False

        if config[key] is None:
            logger.error(f"Configuration key {key} cannot be None")
            return False

    return True


def get_component_theme_colors(component_type: str) -> Dict[str, str]:
    """
    Get theme colors for a component type.

    Args:
        component_type: Type of component (e.g., 'success', 'error', 'info')

    Returns:
        Dict[str, str]: Color configuration
    """
    themes = {
        'success': {
            'bg': 'bg-green-50',
            'border': 'border-green-300',
            'text': 'text-green-700',
            'icon': 'text-green-600'
        },
        'error': {
            'bg': 'bg-red-50',
            'border': 'border-red-300',
            'text': 'text-red-700',
            'icon': 'text-red-600'
        },
        'warning': {
            'bg': 'bg-yellow-50',
            'border': 'border-yellow-300',
            'text': 'text-yellow-700',
            'icon': 'text-yellow-600'
        },
        'info': {
            'bg': 'bg-zinc-50',
            'border': 'border-zinc-300',
            'text': 'text-zinc-700',
            'icon': 'text-zinc-600'
        }
    }

    return themes.get(component_type, themes['info'])


def log_component_event(component_name: str, event: str, details: Optional[Dict[str, Any]] = None):
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
