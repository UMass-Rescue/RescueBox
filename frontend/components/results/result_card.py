import logging
from nicegui import ui
from typing import Callable

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def render_result_card(container: ui.element, result_type: str, result_title: str, result_count: int, on_expand: Callable, job_id: str | None = None) -> None:
    """
    Render a result card with summary and expand action.
    """
    try:
        with container:
            with ui.card().classes('bg-white border border-indigo-200 rounded-xl hover:shadow-lg transition-all duration-300 cursor-pointer group'):
                with ui.row().classes('p-4 items-center justify-between'):
                    # Result type info
                    with ui.column().classes('flex-1'):
                        with ui.row().classes('items-center gap-3'):
                            # icon selection is handled by caller via result_title or styling
                            ui.icon('celebration', size='1.5rem').classes('text-indigo-600')
                            with ui.column():
                                ui.label(result_title).classes('font-semibold text-zinc-800')
                                ui.label(f'{result_count} item{"s" if result_count != 1 else ""}').classes('text-sm text-zinc-500')

                    # Expand button
                    expand_btn = ui.button(
                        'View Details',
                        icon='expand_more'
                    ).classes('rb-brand-primary text-white px-4 py-2 rounded-lg transition-colors z-10')

                    expand_btn.on_click(on_expand)
                    # Make the entire card clickable via an invisible overlay button (placed behind buttons)
                    ui.button('', on_click=on_expand).classes('absolute inset-0 opacity-0 z-0')
    except Exception as e:
        logger.exception("Error rendering result card: %s", e)
