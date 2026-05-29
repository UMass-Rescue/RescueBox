import logging
from nicegui import ui
from typing import Any
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_directory_card(container: ui.element, response: Any) -> None:
    """
    Render a single directory card showing title, path and a simple file list.
    """
    try:
        dir_path = getattr(response, 'path', None)
        title = getattr(response, 'title', None)

        with container:
            with ui.card().classes('bg-indigo-50 border border-indigo-300 p-4'):
                with ui.column().classes('gap-2'):
                    ui.label('📁 Directory Result').classes('font-bold')
                    if title:
                        ui.label(title).classes('text-sm')
                    if dir_path:
                        ui.label(dir_path).classes('text-xs text-zinc-600 font-mono')

                    # List files as plain labels for visibility in tests
                    try:
                        files = sorted(os.listdir(dir_path)) if dir_path and os.path.exists(dir_path) else []
                        ui.label(f'{len(files)} files').classes('text-sm text-zinc-600')
                        if files:
                            # Expose a visible Filename header for tests
                            ui.label('Filename').classes('text-xs font-semibold mt-2')
                            for f in files:
                                ui.label(f).classes('text-xs')
                        else:
                            ui.label('Directory is empty').classes('text-sm text-zinc-500 mt-2')
                    except Exception as e:
                        logger.warning("Error listing directory contents: %s", str(e))
                        ui.label(f'Error listing directory: {str(e)}').classes('text-red-600 text-sm')

                # Open folder button
                if dir_path:
                    ui.button('Open Folder', on_click=lambda p=dir_path: ui.navigate.to(p)).classes('rb-brand-primary text-white mt-2')

    except Exception as e:
        logger.exception("Error rendering directory card: %s", e)
        with container:
            ui.label(f'Error rendering directory: {e}').classes('text-red-600')

