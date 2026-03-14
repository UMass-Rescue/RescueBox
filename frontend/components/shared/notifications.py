import logging
from nicegui import ui
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_loading_row(message: str = "Loading..."):
    """Render a small loading row with spinner and label."""
    with ui.row().classes('items-center gap-2') as loading_row:
        ui.spinner(size='sm')
        ui.label(message).classes('text-sm text-gray-600')
    return loading_row


def render_error_card(container, message: str):
    """Render an error card inside the given container."""
    with container:
        with ui.card().classes('bg-red-50 border border-red-300 p-4') as error_card:
            ui.label('Error').classes('text-lg font-semibold text-red-700 mb-2')
            ui.label(message).classes('text-red-600')
    return error_card


def render_success_card(container, message: str):
    """Render a success card inside the given container."""
    with container:
        with ui.card().classes('bg-green-50 border border-green-300 p-4') as success_card:
            ui.label('Success').classes('text-lg font-semibold text-green-700 mb-2')
            ui.label(message).classes('text-green-600')
    return success_card

"""
Enhanced Notification System

This module provides an enhanced notification system with better styling,
positioning, and user preferences support.

Usage:
    from frontend.components.shared.notifications import notify_success, notify_error, notify_info
    
    notify_success("Job submitted successfully")
    notify_error("Failed to submit job")
    notify_info("Processing your request...")
"""

import logging
from nicegui import ui
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def notify_success(
    message: str,
    duration: float = 3.0,
    position: str = 'top',
    close_button: bool = True
) -> None:
    """
    Show success notification.
    
    Args:
        message: Success message to display
        duration: Duration in seconds (0 = persistent)
        position: Position ('top', 'bottom', 'left', 'right')
        close_button: Whether to show close button
    
    Returns:
        None
    
    Usage:
        notify_success("Job submitted successfully")
    """
    ui.notify(
        message,
        type='positive',
        position=position,
        timeout=int(duration * 1000) if duration > 0 else 0,
        close_button=close_button
    )
    logger.debug("Success notification shown: %s", message)


def notify_error(
    message: str,
    duration: float = 5.0,
    position: str = 'top',
    close_button: bool = True
) -> None:
    """
    Show error notification.
    
    Args:
        message: Error message to display
        duration: Duration in seconds (0 = persistent)
        position: Position ('top', 'bottom', 'left', 'right')
        close_button: Whether to show close button
    
    Returns:
        None
    
    Usage:
        notify_error("Failed to submit job")
    """
    ui.notify(
        message,
        type='negative',
        position=position,
        timeout=int(duration * 1000) if duration > 0 else 0,
        close_button=close_button
    )
    logger.debug("Error notification shown: %s", message)


def notify_info(
    message: str,
    duration: float = 3.0,
    position: str = 'top',
    close_button: bool = True
) -> None:
    """
    Show info notification.
    
    Args:
        message: Info message to display
        duration: Duration in seconds (0 = persistent)
        position: Position ('top', 'bottom', 'left', 'right')
        close_button: Whether to show close button
    
    Returns:
        None
    
    Usage:
        notify_info("Processing your request...")
    """
    ui.notify(
        message,
        type='info',
        position=position,
        timeout=int(duration * 1000) if duration > 0 else 0,
        close_button=close_button
    )
    logger.debug("Info notification shown: %s", message)


def notify_warning(
    message: str,
    duration: float = 4.0,
    position: str = 'top',
    close_button: bool = True
) -> None:
    """
    Show warning notification.
    
    Args:
        message: Warning message to display
        duration: Duration in seconds (0 = persistent)
        position: Position ('top', 'bottom', 'left', 'right')
        close_button: Whether to show close button
    
    Returns:
        None
    
    Usage:
        notify_warning("Please check your input")
    """
    ui.notify(
        message,
        type='warning',
        position=position,
        timeout=int(duration * 1000) if duration > 0 else 0,
        close_button=close_button
    )
    logger.debug("Warning notification shown: %s", message)

