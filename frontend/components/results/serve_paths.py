"""Temporary file serving and OS open helpers for result previews."""

from __future__ import annotations

import logging
import os
import platform
import subprocess
import time
import uuid

from nicegui import app, ui
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import FileResponse as StarletteFileResponse

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.design_tokens import Design

logger = logging.getLogger(__name__)

_SERVED_FILES: dict[str, dict] = {}
_SERVE_TTL = 300

IMAGE_PREVIEW_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".svg",
}


class _ServeRouteState:
    registered = False

    @classmethod
    def mark_registered(cls) -> None:
        cls.registered = True

    @classmethod
    def is_registered(cls) -> bool:
        return cls.registered


def _ensure_serve_route() -> None:
    if _ServeRouteState.is_registered():
        return

    async def _serve_file(_req: Request, token: str, filename: str):
        info = _SERVED_FILES.get(token)
        if not info or time.time() - info.get("created", 0) > _SERVE_TTL:
            _SERVED_FILES.pop(token, None)
            raise HTTPException(404)
        path = info.get("path")
        if not path or not os.path.exists(path) or filename != os.path.basename(path):
            raise HTTPException(404)
        return StarletteFileResponse(path)

    try:
        app.add_api_route("/_serve/{token}/{filename}", _serve_file, methods=["GET"])
        _ServeRouteState.mark_registered()
    except UI_RENDER_ERRORS as e:
        logger.error("Serve route error: %s", e)


def serve_path(file_path: str) -> str:
    _ensure_serve_route()
    now = time.time()
    for t in [
        t for t, i in _SERVED_FILES.items() if now - i.get("created", 0) > _SERVE_TTL
    ]:
        _SERVED_FILES.pop(t, None)
    for t, i in _SERVED_FILES.items():
        if i.get("path") == file_path:
            return f"/_serve/{t}/{os.path.basename(file_path)}"
    t = uuid.uuid4().hex
    _SERVED_FILES[t] = {"path": file_path, "created": now}
    return f"/_serve/{t}/{os.path.basename(file_path)}"


def open_file(path: str) -> None:
    try:
        route = serve_path(path)
        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_PREVIEW_EXTS:
            with ui.dialog() as d, ui.card().classes("max-w-[95vw] w-full p-4"):
                ui.label(os.path.basename(path)).classes("text-lg font-semibold")
                ui.image(route).props("fit=contain").classes("w-full max-h-[85vh]")
                ui.label(path).classes("text-xs font-mono text-zinc-600 break-all")
                with ui.row().classes("gap-2 mt-2"):
                    ui.button(
                        "Open folder",
                        color=None,
                        on_click=lambda: open_folder(os.path.dirname(path)),
                    ).classes(Design.BTN_SECONDARY_NEUTRAL)
                    ui.button("Close", color=None, on_click=d.close).classes(
                        Design.BTN_MEDIUM_GRAY
                    )
            d.open()
        else:
            ui.navigate.to(route)
    except UI_RENDER_ERRORS as e:
        logger.error("Open file error: %s", e)
        ui.notify(f"Error opening file: {e}", type="negative")


def open_folder(path: str) -> None:
    if not path:
        ui.notify("Invalid folder path", type="negative")
        return
    if not os.path.exists(path):
        ui.notify("Folder not found", type="negative")
        return
    if not os.path.isdir(path):
        ui.notify("Path is not a folder", type="negative")
        return
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except UI_RENDER_ERRORS as e:
        logger.error("Open folder error: %s", e)
        ui.notify(f"Failed to open folder: {e}", type="negative")
