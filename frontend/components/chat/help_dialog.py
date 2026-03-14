import logging
from nicegui import ui
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def show_help_dialog(help_text: str, title: Optional[str] = "RescueBox Help") -> None:
    """
    Show help text in a large dialog optimized for readability.
    """
    try:
        # Larger, more readable dialog: wider max-width and taller max-height.
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-7xl max-h-[85vh] overflow-hidden'):
            # Header with stronger contrast and larger title
            with ui.row().classes('items-center justify-between bg-gradient-to-r from-blue-700 to-indigo-600 text-white p-4'):
                ui.label(title).classes('text-2xl font-bold')
                # Small subtitle for context
                # ui.label('Rescuebox Usage').classes('text-sm text-red-100').style('margin-left: 1rem')
                ui.button('Close', on_click=dialog.close).classes('bg-transparent text-white')

            # Content area with a comfortable reading width and larger typography
            with ui.scroll_area().classes('p-6'):
                with ui.column().classes('gap-4'):
                    # Render markdown with larger prose styles and ensure preformatted blocks wrap
                    ui.markdown(help_text).classes('prose prose-lg lg:prose-xl max-w-none text-gray-900 leading-relaxed whitespace-pre-wrap')

        dialog.open()
    except Exception as e:
        logger.exception("Failed to open help dialog: %s", e)
