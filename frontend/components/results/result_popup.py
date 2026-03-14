from nicegui import ui
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def show_result_popup(root: Dict[str, Any], title: str = "Result", response_dict: Dict[str, Any] = None):
    """
    Create and open a result popup that renders the given root using ResultsPreview.
    """
    try:
        from frontend.components.results.result_popup_component import show_result_popup_component
        return show_result_popup_component(root, title=title, response_dict=response_dict)
    except Exception as e:
        logger.exception("Failed to delegate to result_popup_component: %s", e)
        # Fallback to original inline popup
        try:
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl max-h-[80vh]'):
                ui.label(title).classes('text-2xl font-bold mb-4')
                # Content container
                content = ui.column().classes('overflow-auto')
                try:
                    from frontend.components.results.results_preview import ResultsPreview
                    ResultsPreview.render(content, {'root': root})
                except Exception as e2:
                    logger.exception("Failed to render result in popup (fallback): %s", e2)
                    ui.label(f'Error rendering result: {e2}').classes('text-red-600')
            dialog.open()
            return dialog
        except Exception:
            logger.debug("Failed to open fallback result dialog")
            return None

