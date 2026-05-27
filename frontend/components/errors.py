import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import logging
from nicegui import ui
from typing import Optional, Any, List





def render_error_boundary(
    container: ui.element,
    title: str,
    message: str,
    technical_details: Optional[str] = None,
    icon: str = "error",
    extra_actions: Optional[List[Any]] = None
) -> None:
    """
    Render a standardized error boundary inside `container`.
    `extra_actions` may contain callables that will be rendered as buttons.
    """
    try:
        with container:
            with ui.card().classes('bg-red-50 border-2 border-red-300 rounded-lg p-4'):
                with ui.row().classes('items-start gap-4'):
                    ui.icon(icon, size='3rem').classes('text-red-600')
                    with ui.column().classes('flex-1'):
                        ui.label(f'🚫 {title}').classes('text-xl font-bold text-red-800 mb-2')
                        ui.label(message).classes('text-sm text-red-700')
                        if technical_details:
                            with ui.expansion('Technical Details'):
                                ui.code(technical_details).classes('text-xs max-h-48 overflow-auto')

                if extra_actions:
                    with ui.row().classes('gap-2 mt-4'):
                        for action in extra_actions:
                            try:
                                # action should be a tuple (label, on_click_callable, classes)
                                label, callback, classes = action
                                ui.button(label, on_click=callback).classes(classes)
                            except Exception as e:
                                logger.exception("Error rendering error message component: %s", e)
    except Exception as e:
        logger.exception("Error rendering error boundary: %s", e)



import logging
from nicegui import ui
from typing import Any, Optional





def render_error_message(container: ui.element, message: str, details: Optional[str] = None, debug_data: Any = None) -> None:
    """
    Render a compact error message into the given container.
    """
    try:
        with container:
            with ui.card().classes('bg-red-50 border border-red-300 p-4'):
                ui.label(f'❌ {message}').classes('text-red-600 font-semibold')
                if details:
                    ui.label(details).classes('text-zinc-600 text-sm mt-2')
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



import logging
from typing import List

from nicegui import ui

from frontend.design_tokens import Design





def show_validation_dialog(primary_error: str, additional_errors: List[str] | None = None) -> ui.dialog:
    """
    Show a modal validation dialog listing primary and additional errors.
    Returns the dialog instance (already opened).
    """
    with ui.dialog() as error_dialog:
        with ui.card().classes('max-w-md'):
            ui.label('Validation Error').classes('text-lg font-bold text-[#505759] mb-4')
            ui.label(primary_error).classes('mb-4')
            if additional_errors:
                ui.label('Additional errors:').classes('font-semibold mb-2')
                for additional_error in additional_errors:
                    ui.label(f'• {additional_error}').classes('mb-1')
            ui.button('OK', on_click=error_dialog.close).classes(f'mt-4 {Design.BTN_MEDIUM_GRAY}')
    error_dialog.open()
    logger.debug("Validation dialog opened with primary_error: %s", primary_error)
    return error_dialog

