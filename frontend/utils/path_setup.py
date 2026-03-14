"""
Path Setup Utilities

This module provides utilities for setting up Python path to access backend models.
It centralizes the sys.path manipulation that was previously duplicated across many files.

Usage:
    from frontend.utils.path_setup import setup_backend_path
    setup_backend_path()
    from rb.api.models import TaskSchema
"""

import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Cache to track if path has been set up
_path_setup_done = False


def setup_backend_path(backend_path: Optional[Path] = None):
    """
    Add backend src directory to sys.path if not already present.
    
    This function ensures that backend models (rb.api.models, etc.) can be imported
    from frontend code. It only adds the path once, even if called multiple times.
    
    Args:
        backend_path: Optional custom path to backend src directory.
                     If not provided, uses default: project_root/src
    
    Returns:
        None
    
    Usage:
        from frontend.utils.path_setup import setup_backend_path
        setup_backend_path()
        from rb.api.models import TaskSchema
    
    Tips:
    - This function is idempotent - safe to call multiple times
    - The path is added to the beginning of sys.path for priority
    - Logs a warning if the backend path doesn't exist
    """
    global _path_setup_done
    
    if _path_setup_done:
        logger.debug("Backend path already set up, skipping")
        return
    
    if backend_path is None:
        # Default: project_root/src (where project_root is frontend's parent)
        frontend_dir = Path(__file__).parent.parent
        backend_path = frontend_dir.parent / 'src'
    
    backend_path_str = str(backend_path.resolve())
    
    if not backend_path.exists():
        logger.warning("Backend path does not exist: %s", backend_path)
        return
    
    if backend_path_str not in sys.path:
        sys.path.insert(0, backend_path_str)
        logger.debug("Added backend path to sys.path: %s", backend_path_str)
    else:
        logger.debug("Backend path already in sys.path: %s", backend_path_str)
    
    _path_setup_done = True
    logger.info("Backend path setup completed")


# Auto-setup on import (optional - can be removed if explicit setup is preferred)
# setup_backend_path()

