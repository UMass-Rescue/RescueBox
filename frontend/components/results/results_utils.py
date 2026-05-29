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

from frontend.design_tokens import Design
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

SERVE_TTL = 300  # seconds

# Extensions for which we show an in-app preview dialog (stay on results page + open folder).
_IMAGE_PREVIEW_EXTENSIONS = frozenset({
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tif', '.tiff', '.svg',
})


def _ensure_serve_route_registered() -> None:
    global _SERVE_ROUTE_REGISTERED

    async def _serve_file_endpoint(_request: Request, token: str, filename: str):
        info = _SERVED_FILES.get(token)
        if not info:
            raise HTTPException(status_code=404)
        if time.time() - info.get('created', 0) > SERVE_TTL:
            _SERVED_FILES.pop(token, None)
            raise HTTPException(status_code=404)
        path = info.get('path')
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404)
        expected_basename = os.path.basename(path)
        if filename != expected_basename:
            raise HTTPException(status_code=404)
        return FileResponse(path)

    if not _SERVE_ROUTE_REGISTERED:
        try:
            app.add_api_route('/_serve/{token}/{filename}', _serve_file_endpoint, methods=['GET'])
            _SERVE_ROUTE_REGISTERED = True
        except Exception as e:
            logger.error("Failed to register serve route: %s", e)


def _cleanup_expired_served_files() -> None:
    now = time.time()
    expired = [t for t, info in _SERVED_FILES.items() if now - info.get('created', 0) > SERVE_TTL]
    for t in expired:
        _SERVED_FILES.pop(t, None)


def _serve_route_for_path(file_path: str) -> str:
    """
    Register ``file_path`` for HTTP serving (or reuse an existing token) and
    return the app-relative URL ``/_serve/{token}/{basename}``.
    """
    _ensure_serve_route_registered()
    _cleanup_expired_served_files()

    for token, info in _SERVED_FILES.items():
        if info.get('path') == file_path:
            return f"/_serve/{token}/{os.path.basename(file_path)}"

    token = uuid.uuid4().hex
    _SERVED_FILES[token] = {'path': file_path, 'created': time.time()}
    return f"/_serve/{token}/{os.path.basename(file_path)}"


def open_text_markdown_modal(filename: str, body: str) -> None:
    """
    Show full text (e.g. summary ``.txt``) in a scrollable modal.

    Uses a readonly ``textarea`` so plain ``.txt`` always shows reliably (``ui.markdown``
    inside flex ``scroll_area`` can collapse to an empty-looking view for some payloads).
    """
    text = body if body is not None else ""
    with ui.dialog() as dialog, ui.card().classes(
        'max-w-[92vw] w-[min(56rem,92vw)] max-h-[90vh] flex flex-col p-4 gap-3'
    ):
        ui.label(filename or 'Document').classes('text-lg font-semibold shrink-0 text-zinc-900')
        with ui.scroll_area().classes(
            'w-full min-h-[50vh] max-h-[75vh] border border-zinc-200 rounded-lg bg-white'
        ):
            if text.strip():
                ui.textarea(value=text).props(
                    'readonly outlined dense input-class=font-mono'
                ).classes('w-full min-h-[48vh]').style('white-space: pre-wrap')
            else:
                ui.label('No content').classes('text-zinc-500 italic p-4')
        with ui.row().classes('justify-end shrink-0'):
            ui.button('Close', on_click=dialog.close).classes(Design.BTN_MEDIUM_GRAY)
    dialog.open()


def _open_image_preview_dialog(file_path: str, route: str) -> None:
    """Show image in a modal with path and quick access to the containing folder."""
    folder = os.path.dirname(file_path)
    name = os.path.basename(file_path)
    with ui.dialog() as dialog, ui.card().classes('max-w-[95vw] w-full p-4'):
        ui.label(name).classes('text-lg font-semibold')
        # QImg defaults to fit=cover (crops); contain scales the whole image inside the box.
        ui.image(route).props('fit=contain').classes('w-full max-h-[85vh]')
        ui.label(file_path).classes('text-xs font-mono break-all text-zinc-600')
        with ui.row().classes('gap-2 flex-wrap mt-2'):
            if folder:
                ui.button('Open folder', icon='folder_open', on_click=lambda f=folder: open_folder(f)).props(
                    'outline'
                )
            ui.button('Close', on_click=dialog.close).classes(Design.BTN_MEDIUM_GRAY)
    dialog.open()


def open_file(file_path: str):
    """
    Open a file for viewing.

    Images are shown in an in-app dialog (served via ``/_serve/...``) with the
    full path and an **Open folder** action to the parent directory. Other
    file types still navigate the browser to the served URL directly.

    Tokens expire after ``SERVE_TTL`` seconds and are cleaned up on each request.
    """
    logger.debug("Serving file via HTTP: %s", file_path)

    try:
        route = _serve_route_for_path(file_path)
    except Exception as e:
        logger.error("Failed to register served file: %s", e)
        ui.notify(f'Error opening file: {str(e)}', type='negative', classes='rb-notify-505759')
        return

    ext = os.path.splitext(file_path)[1].lower()
    if ext in _IMAGE_PREVIEW_EXTENSIONS:
        logger.debug("Served file via HTTP at %s (image preview dialog)", route)
        _open_image_preview_dialog(file_path, route)
        return

    try:
        ui.navigate.to(route)
        logger.debug("Served file via HTTP at %s", route)
    except Exception as e:
        logger.error("Failed to navigate to served file %s: %s", route, e)
        ui.notify(f'Error opening file: {str(e)}', type='negative', classes='rb-notify-505759')


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
        ui.notify('Invalid folder path', type='negative', classes='rb-notify-505759')
        return
    
    try:
        # Validate folder exists
        if not os.path.exists(folder_path):
            error_msg = f'Folder not found: {folder_path}'
            logger.warning(error_msg)
            ui.notify(error_msg, type='negative', classes='rb-notify-505759')
            return
        
        if not os.path.isdir(folder_path):
            error_msg = f'Path is not a folder: {folder_path}'
            logger.warning(error_msg)
            ui.notify(error_msg, type='negative', classes='rb-notify-505759')
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
        ui.notify(error_msg, type='negative', classes='rb-notify-505759')
    except PermissionError as e:
        error_msg = f'Permission denied opening folder: {folder_path}'
        logger.error(error_msg, exc_info=True)
        ui.notify(error_msg, type='negative', classes='rb-notify-505759')
    except subprocess.CalledProcessError as e:
        error_msg = f'Failed to open folder: {str(e)}'
        logger.error(error_msg, exc_info=True)
        ui.notify(error_msg, type='negative', classes='rb-notify-505759')
    except Exception as e:
        error_msg = f'Error opening folder: {str(e)}'
        logger.error(error_msg, exc_info=True)
        ui.notify(error_msg, type='negative', classes='rb-notify-505759')

