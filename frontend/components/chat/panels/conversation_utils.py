"""
Conversation Utilities

This module provides utility functions for conversation handling.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _format_timestamp(timestamp: str) -> str:
    """
    Format timestamp for display.

    Args:
        timestamp: ISO format timestamp string

    Returns:
        str: Formatted timestamp string
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt

        if diff.days == 0:
            if diff.seconds < 3600:
                return f"{diff.seconds // 60} minutes ago"
            return f"{diff.seconds // 3600} hours ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime('%Y-%m-%d')
    except Exception:
        return timestamp
