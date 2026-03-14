import logging
from nicegui import ui

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_file_browser_header(title: str = "Select Directory", icon: str = "folder_open") -> None:
    """
    Render a standardized header for file/directory browser dialogs.
    """
    with ui.row().classes('bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 items-center'):
        # Use yellow folder icon to mimic Windows Explorer
        ui.icon(icon, size='2rem').classes('mr-3 text-yellow-400')
        ui.label(title).classes('text-xl font-semibold')

