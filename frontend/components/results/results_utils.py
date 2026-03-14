"""
Results Preview Utilities

This module provides utility functions for results preview operations,
including platform-specific file and folder opening.
"""

import logging
import os
import subprocess
import platform
from nicegui import ui
from nicegui import app
from starlette.responses import FileResponse
import uuid
from typing import Dict
from starlette.requests import Request
import time
from starlette.exceptions import HTTPException

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_SERVED_FILES: Dict[str, Dict] = {}
_SERVE_ROUTE_REGISTERED = False


def open_file(file_path: str):
    """
    Serve file via HTTP and navigate the client to it.

    This approach provides consistent behavior across desktop and container
    environments by serving files through the app and directing the browser to
    the served URL. Tokens expire after SERVE_TTL seconds and are cleaned up
    on each serve request.
    """
    logger.debug("Serving file via HTTP: %s", file_path)

    SERVE_TTL = 300  # seconds
    global _SERVE_ROUTE_REGISTERED

    def _cleanup_expired():
        now = time.time()
        expired = [t for t, info in _SERVED_FILES.items() if now - info.get('created', 0) > SERVE_TTL]
        for t in expired:
            _SERVED_FILES.pop(t, None)

    async def _serve_file_endpoint(_request: Request, token: str, filename: str):
        info = _SERVED_FILES.get(token)
        if not info:
            raise HTTPException(status_code=404)
        # ensure token is not expired
        if time.time() - info.get('created', 0) > SERVE_TTL:
            _SERVED_FILES.pop(token, None)
            raise HTTPException(status_code=404)
        path = info.get('path')
        # verify path exists
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404)
        # security: confirm requested filename matches actual file basename
        expected_basename = os.path.basename(path)
        if filename != expected_basename:
            raise HTTPException(status_code=404)
        return FileResponse(path)

    # Register the single serving route once
    if not _SERVE_ROUTE_REGISTERED:
        try:
            app.add_api_route('/_serve/{token}/{filename}', _serve_file_endpoint, methods=['GET'])
            _SERVE_ROUTE_REGISTERED = True
        except Exception as e:
            logger.error("Failed to register serve route: %s", e)

    # Cleanup expired tokens
    _cleanup_expired()

    # Reuse existing token if the path is already served
    for token, info in _SERVED_FILES.items():
        if info.get('path') == file_path:
            route = f"/_serve/{token}/{os.path.basename(file_path)}"
            try:
                ui.navigate.to(route)
                logger.debug("Navigating to existing served file route %s", route)
            except Exception as e:
                logger.error("Failed to navigate to existing route %s: %s", route, e)
                ui.notify(f'Error opening file: {str(e)}', type='negative')
            return

    # Create new token and serve
    token = uuid.uuid4().hex
    _SERVED_FILES[token] = {'path': file_path, 'created': time.time()}
    route = f"/_serve/{token}/{os.path.basename(file_path)}"
    try:
        ui.navigate.to(route)
        logger.debug("Served file via HTTP at %s", route)
    except Exception as e:
        logger.error("Failed to navigate to served file %s: %s", route, e)
        ui.notify(f'Error opening file: {str(e)}', type='negative')


def open_folder(folder_path: str):
    """
    Open folder in file explorer.
    
    Uses platform-specific commands to open folders in the default file explorer.
    
    Args:
        folder_path (str): Path to the folder to open
    
    Returns:
        None
    
    Raises:
        Exception: If folder opening fails (logged and shown as notification)
    
    Tips:
    - Windows: Uses os.startfile()
    - macOS: Uses 'open' command
    - Linux: Uses 'xdg-open' command
    - Errors are shown as UI notifications
    """
    logger.debug("Opening folder: %s", folder_path)
    
    if not folder_path:
        logger.warning("Attempted to open empty folder path")
        ui.notify('Invalid folder path', type='negative')
        return
    
    try:
        # Validate folder exists
        if not os.path.exists(folder_path):
            error_msg = f'Folder not found: {folder_path}'
            logger.warning(error_msg)
            ui.notify(error_msg, type='negative')
            return
        
        if not os.path.isdir(folder_path):
            error_msg = f'Path is not a folder: {folder_path}'
            logger.warning(error_msg)
            ui.notify(error_msg, type='negative')
            return
        
        if platform.system() == 'Windows':
            os.startfile(folder_path)
        elif platform.system() == 'Darwin':
            subprocess.run(['open', folder_path], check=True)
        else:
            subprocess.run(['xdg-open', folder_path], check=True)
        logger.debug("Folder opened successfully")
    except FileNotFoundError as e:
        error_msg = f'Folder not found: {folder_path}'
        logger.error(error_msg, exc_info=True)
        ui.notify(error_msg, type='negative')
    except PermissionError as e:
        error_msg = f'Permission denied opening folder: {folder_path}'
        logger.error(error_msg, exc_info=True)
        ui.notify(error_msg, type='negative')
    except subprocess.CalledProcessError as e:
        error_msg = f'Failed to open folder: {str(e)}'
        logger.error(error_msg, exc_info=True)
        ui.notify(error_msg, type='negative')
    except Exception as e:
        error_msg = f'Error opening folder: {str(e)}'
        logger.error(error_msg, exc_info=True)
        ui.notify(error_msg, type='negative')

