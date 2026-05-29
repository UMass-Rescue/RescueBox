from typing import Any
from nicegui import ui
import os
import webbrowser
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _open_file(path: str) -> None:
    """
    Open a file path. Prefer client-side `ui.open` when available; otherwise
    fall back to a server-side open (best-effort) or OS-native open on Windows.
    """
    try:
        navigator = getattr(ui, 'navigate', None)
        if navigator and callable(getattr(navigator, 'to', None)):
            navigator.to(path)
            return

        # Try OS-native open on Windows
        try:
            if os.name == 'nt':
                os.startfile(path)  # type: ignore[attr-defined]
                return
        except Exception:
            pass

        webbrowser.open(path)
    except Exception as e:
        logger.info("Open file requested but failed to open: %s (%s)", path, str(e))


def _open_folder(path: str) -> None:
    """
    Open the folder containing `path`. Uses client-side `ui.open` if available,
    otherwise falls back to OS-native folder opening or webbrowser.
    """
    try:
        folder = os.path.dirname(path) or path
        navigator = getattr(ui, 'navigate', None)
        if navigator and callable(getattr(navigator, 'to', None)):
            navigator.to(folder)
            return

        try:
            if os.name == 'nt':
                os.startfile(folder)  # type: ignore[attr-defined]
                return
        except Exception:
            pass

        webbrowser.open(folder)
    except Exception as e:
        logger.info("Open folder requested but failed to open: %s (%s)", path, str(e))



def render_file_card(container: ui.element, response: Any) -> None:
    """
    Render a single file card. Accepts either a Pydantic FileResponse model
    or a dict with compatible keys.
    """
    try:
        path = getattr(response, 'path', response.get('path') if isinstance(response, dict) else None)
        title = getattr(response, 'title', response.get('title') if isinstance(response, dict) else None)
        file_type = getattr(response, 'file_type', None)
        display_title = title or (os.path.basename(path) if path else 'File Result')

        with container:
            with ui.card().classes('bg-white p-4'):
                # Stable heading expected by tests
                ui.label('📄 File Result').classes('font-bold')
                with ui.row().classes('items-center justify-between'):
                    ui.label(display_title).classes('text-lg font-semibold')
                    with ui.row().classes('gap-2'):
                        if path:
                            ui.button('Open File', on_click=lambda p=path: _open_file(p)).classes('rb-brand-primary text-white px-3 py-1')
                            ui.button('Open Folder', on_click=lambda p=path: _open_folder(p)).classes(
                                'border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 '
                                'text-zinc-800 px-3 py-1 rounded-lg text-sm font-medium'
                            )

                if file_type and getattr(file_type, 'value', str(file_type)) in ('img', 'image', 'png', 'jpg', 'jpeg'):
                    try:
                        ui.image(path).classes('w-full h-48 object-cover mt-2')
                    except Exception:
                        logger.debug("Could not preview image at path: %s", path)
                else:
                    if path:
                        ui.label(path).classes('text-sm font-mono mt-2 text-zinc-600')
    except Exception as e:
        logger.exception("render_file_card error: %s", e)
        with container:
            ui.label(f'Error displaying file card: {e}').classes('text-red-600')

