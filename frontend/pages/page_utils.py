"""
Page Utilities

This module provides shared utilities and constants for all pages.
"""

import logging
from typing import Dict, Any, Optional
from frontend.constants import UI_TITLES

# Configure logging for page utilities
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_page_title(page_key: str, default: str = "Page") -> str:
    """
    Get the title for a page from constants.

    Args:
        page_key: Key to look up in UI_TITLES
        default: Default title if key not found

    Returns:
        str: The page title
    """
    return UI_TITLES.get(page_key, default)


def setup_common_imports():
    """
    Setup commonly used imports for pages.

    This function can be called by page modules to ensure
    consistent import setup.
    """
    # Common imports that most pages need
    from frontend.utils.path_setup import setup_backend_path
    setup_backend_path()


def create_page_metadata(page_name: str) -> Dict[str, Any]:
    """
    Create metadata for a page.

    Args:
        page_name: Name of the page

    Returns:
        Dict[str, Any]: Page metadata
    """
    return {
        'name': page_name,
        'title': get_page_title(page_name.lower(), page_name),
        'route': f'/{page_name.lower()}',
    }


def log_page_action(page_name: str, action: str, details: Optional[str] = None):
    """
    Log a page-related action.

    Args:
        page_name: Name of the page
        action: Action being performed
        details: Additional details
    """
    message = f"{page_name} page: {action}"
    if details:
        message += f" - {details}"

    logger.debug(message)
