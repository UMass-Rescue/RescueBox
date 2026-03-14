import logging
from nicegui import ui
from typing import Any, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_error_message(container: ui.element, message: str, details: Optional[str] = None, debug_data: Any = None) -> None:
    """
    Render a compact error message into the given container.
    """
    try:
        with container:
            with ui.card().classes('bg-red-50 border border-red-300 p-4'):
                ui.label(f'❌ {message}').classes('text-red-600 font-semibold')
                if details:
                    ui.label(details).classes('text-gray-600 text-sm mt-2')
                if debug_data is not None:
                    with ui.expansion('Details').classes('mt-4'):
                        ui.label('Debug Information:').classes('font-semibold mb-2')
                        ui.code(str(debug_data), language='json').classes('text-xs max-h-32 overflow-auto')
    except Exception as e:
        logger.exception("Error rendering error message component: %s", e)
        try:
            with container:
                ui.label(f'Error: {message}').classes('text-red-600')
        except Exception:
            logger.debug("Failed to render fallback simple error label")

