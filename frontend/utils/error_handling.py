"""
Standardized Error Handling Utilities

This module provides consistent error handling patterns across the frontend.
It standardizes how errors are logged, displayed to users, and handled.

Usage:
    from frontend.utils.error_handling import handle_api_error, show_error_to_user
    
    try:
        response = await api_client.get('/models')
        response.raise_for_status()
    except httpx.HTTPError as e:
        await handle_api_error(e, "Failed to fetch models")
"""

import logging
from typing import Optional, Union, Any
from nicegui import ui
import httpx

# Try to use enhanced notifications if available, fallback to ui.notify
try:
    from frontend.components.shared.notifications import (
        notify_success,
        notify_error,
        notify_info,
        notify_warning
    )
    _ENHANCED_NOTIFICATIONS = True
except ImportError:
    _ENHANCED_NOTIFICATIONS = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def handle_api_error(
    error: Exception,
    context: str,
    show_to_user: bool = True,
    user_message: Optional[str] = None,
    log_level: str = 'error'
) -> None:
    """
    Standardized API error handling.
    
    Logs the error with context and optionally displays a user-friendly message.
    
    Args:
        error: The exception that occurred
        context: Description of what operation failed (for logging)
        show_to_user: Whether to show error notification to user
        user_message: Custom message to show user (defaults to generic message)
        log_level: Logging level ('error', 'warning', 'info')
    
    Returns:
        None
    
    Usage:
        try:
            response = await api_client.get('/models')
            response.raise_for_status()
        except httpx.HTTPError as e:
            await handle_api_error(
                e,
                "Failed to fetch models",
                user_message="Unable to load models. Please try again."
            )
    
    Tips:
    - Always provide meaningful context for debugging
    - Use user_message for user-friendly error text
    - Set log_level to 'warning' for expected errors (e.g., 404)
    """
    log_func = getattr(logger, log_level.lower(), logger.error)
    log_func(f"{context}: {error}", exc_info=True)
    
    if show_to_user:
        message = user_message or "An error occurred. Please try again."
        if _ENHANCED_NOTIFICATIONS:
            notify_error(message)
        else:
            ui.notify(message, type='negative')
        logger.debug("Error notification shown to user: %s", message)


def show_error_to_user(message: str, type: str = 'negative') -> None:
    """
    Show error notification to user.
    
    Convenience function for displaying error messages.
    Uses enhanced notifications if available.
    
    Args:
        message: Error message to display
        type: Notification type ('negative', 'warning', 'info')
    
    Returns:
        None
    
    Usage:
        show_error_to_user("Failed to save job")
    """
    if _ENHANCED_NOTIFICATIONS:
        if type == 'negative':
            notify_error(message)
        elif type == 'warning':
            notify_warning(message)
        else:
            notify_info(message)
    else:
        ui.notify(message, type=type)
    logger.debug("Error notification shown: %s", message)


def show_success_to_user(message: str) -> None:
    """
    Show success notification to user.
    
    Convenience function for displaying success messages.
    Uses enhanced notifications if available.
    
    Args:
        message: Success message to display
    
    Returns:
        None
    
    Usage:
        show_success_to_user("Job submitted successfully")
    """
    if _ENHANCED_NOTIFICATIONS:
        notify_success(message)
    else:
        ui.notify(message, type='positive')
    logger.debug("Success notification shown: %s", message)


def handle_validation_error(
    errors: Union[dict, list],
    context: str = "Form validation failed"
) -> None:
    """
    Handle form validation errors with specific, actionable messages.

    Logs validation errors and shows user-friendly, specific error messages
    that help users understand and fix the problem.

    Args:
        errors: Validation errors (dict or list)
        context: Context for logging

    Returns:
        None

    Usage:
        try:
            validate_form_data(data, schema)
        except ValidationError as e:
            handle_validation_error(e.errors(), "Job form validation")
    """
    logger.warning("%s: %s", context, errors)

    # Provide specific, actionable error messages
    error_messages = []

    if isinstance(errors, dict):
        for field, error in errors.items():
            if isinstance(error, str):
                error_msg = error
            else:
                error_msg = str(error)

            logger.info("Processing error for field '%s': %s", field, error_msg)

            # Provide specific help for common validation errors
            if "Path does not point to a directory" in error_msg:
                error_messages.append(f"📁 {field}: Please select a valid directory using the 'Browse' button")
            elif "Path does not exist" in error_msg or "No such file or directory" in error_msg:
                error_messages.append(f"📁 {field}: The selected path does not exist")
            elif "Path does not point to a file" in error_msg:
                error_messages.append(f"📄 {field}: Please select a valid file using the 'Browse' button")
            elif "does not point to" in error_msg:
                # Catch any other path validation errors
                error_messages.append(f"📁 {field}: {error_msg} - Please use the 'Browse' button to select a valid path")
            else:
                error_messages.append(f"⚠️ {field}: {error_msg}")

    # Show the most specific error message first
    if error_messages:
        primary_error = error_messages[0]
        logger.info("Showing validation error to user: %s", primary_error)

        # Show validation dialog only
        try:
            from frontend.components.errors.validation_dialog import show_validation_dialog
            show_validation_dialog(primary_error, error_messages[1:] if len(error_messages) > 1 else None)
        except Exception:
            # Fallback inline dialog if component unavailable
            with ui.dialog() as error_dialog:
                with ui.card().classes('max-w-md'):
                    ui.label('Validation Error').classes('text-lg font-bold text-red-600 mb-4')
                    ui.label(primary_error).classes('mb-4')
                    if len(error_messages) > 1:
                        ui.label('Additional errors:').classes('font-semibold mb-2')
                        for additional_error in error_messages[1:]:
                            ui.label(f'• {additional_error}').classes('mb-1')
                    ui.button('OK', on_click=error_dialog.close).classes('mt-4')
            error_dialog.open()

        # Log additional errors if there are multiple
        if len(error_messages) > 1:
            logger.info("Additional validation errors: %s", error_messages[1:])

    else:
        # Fallback for unexpected error formats
        logger.warning("No specific error messages generated, using fallback")
        ui.notify("Please check the form for errors", type='warning')

    logger.debug("Validation error notification shown")

