import logging
from nicegui import ui
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def show_result_popup_component(root: Dict[str, Any], title: str = "Result", response_dict: Optional[Dict[str, Any]] = None):
    """
    Create and open a result popup that renders the given root using ResultsPreview.
    """
    try:
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl max-h-[80vh]'):
            ui.label(title).classes('text-2xl font-bold mb-4')
            # Content container
            content = ui.column().classes('overflow-auto')
            try:
                from frontend.components.results.results_preview import ResultsPreview
                ResultsPreview.render(content, {'root': root})
            except Exception as e:
                logger.exception("Failed to render result in popup component: %s", e)
                ui.label(f'Error rendering result: {e}').classes('text-red-600')
        dialog.open()
        return dialog
    except Exception as e:
        logger.exception("Failed to create result popup component: %s", e)
        # best-effort fallback
        try:
            with ui.dialog() as dialog:
                ui.label(title)
                ui.label(f'Error showing result: {e}')
            dialog.open()
            return dialog
        except Exception:
            logger.debug("Could not show fallback dialog for result popup")
            return None

