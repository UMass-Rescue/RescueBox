"""Page Utilities This module provides shared utilities and constants for all pages."""

import logging
from typing import Any

from frontend.constants import UI_TITLES

# Configure logging for page utilities
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_page_title(page_key: str, default: str = "Page") -> str:
    """Get the title for a page from constants. Args:"""
    return UI_TITLES.get(page_key, default)


def create_page_metadata(page_name: str) -> dict[str, Any]:
    """Create metadata for a page. Args:"""
    return {
        "name": page_name,
        "title": get_page_title(page_name.lower(), page_name),
        "route": f"/{page_name.lower()}",
    }


def log_page_action(page_name: str, action: str, details: str | None = None):
    """Log a page-related action. Args:"""
    message = f"{page_name} page: {action}"
    if details:
        message += f" - {details}"

    logger.debug(message)
