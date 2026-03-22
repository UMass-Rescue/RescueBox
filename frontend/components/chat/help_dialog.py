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
        # Large modal: use most of viewport to minimize scrolling
        with ui.dialog() as dialog, ui.card().classes(
            'w-[95vw] max-w-[1400px] max-h-[95vh] overflow-hidden'
        ):
            # Header with stronger contrast and larger title
            with ui.row().classes('items-center justify-between bg-gradient-to-r from-blue-700 to-indigo-600 text-white p-4'):
                ui.label(title).classes('text-2xl font-bold')
                ui.button('Close', on_click=dialog.close).classes('bg-transparent text-white')

            # Content area with explicit height so content renders and scrolls
            with ui.scroll_area().classes('p-6 h-[calc(95vh-5rem)]'):
                with ui.column().classes('gap-4'):
                    # Render markdown with larger prose styles and ensure preformatted blocks wrap
                    ui.markdown(help_text).classes('prose prose-lg lg:prose-xl max-w-none text-gray-900 leading-relaxed whitespace-pre-wrap')

        dialog.open()
    except Exception as e:
        logger.exception("Failed to open help dialog: %s", e)
