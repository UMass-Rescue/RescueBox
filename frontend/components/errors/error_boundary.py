import logging
from nicegui import ui
from typing import Optional, Any, List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
                            except Exception:
                                # best-effort: render a disabled button
                                ui.button('Action', disabled=True).classes('bg-zinc-300')
    except Exception as e:
        logger.exception("Error rendering error boundary: %s", e)
        # Fallback minimal display
        try:
            with container:
                ui.label(f"Error: {title} - {message}").classes('text-red-600')
        except Exception:
            logger.debug("Failed to render fallback error label")

