"""
Logs Utilities

This module provides utilities for log file processing and display.
"""

import logging
from pathlib import Path
from typing import List, Optional

# Configure logging for logs package
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def read_log_file(log_file_path: Path, max_lines: int = 1000) -> str:
    """
    Read and process log file contents.

    Args:
        log_file_path: Path to the log file
        max_lines: Maximum number of lines to read (to prevent memory issues)

    Returns:
        str: Processed log content
    """
    try:
        if not log_file_path.exists():
            return f"Log file does not exist: {log_file_path}"

        logger.debug(f"Reading log file: {log_file_path}")

        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        # Limit to max_lines for performance
        if len(lines) > max_lines:
            lines = lines[-max_lines:]
            content = f"[Showing last {max_lines} lines of {len(lines) + (len(lines) - max_lines)} total lines]\n\n"
        else:
            content = ""

        content += ''.join(lines)
        return content

    except Exception as e:
        error_msg = f"Error reading log file: {str(e)}"
        logger.error(error_msg)
        return error_msg


def format_log_content(content: str) -> str:
    """
    Format log content for display.

    Args:
        content: Raw log content

    Returns:
        str: Formatted log content
    """
    # Basic formatting - could be enhanced with syntax highlighting
    return content.strip()


def get_log_file_info(log_file_path: Path) -> dict:
    """
    Get information about the log file.

    Args:
        log_file_path: Path to the log file

    Returns:
        dict: File information
    """
    info = {
        'path': str(log_file_path),
        'exists': log_file_path.exists(),
        'size': 0,
        'modified': None
    }

    if log_file_path.exists():
        stat = log_file_path.stat()
        info['size'] = stat.st_size
        info['modified'] = stat.st_mtime

    return info
