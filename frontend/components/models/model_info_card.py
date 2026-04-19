import logging
from nicegui import ui
from typing import Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_model_info_card(container: ui.element, model_info: Any, model_info_dict: Dict[str, Any], server_status: str) -> None:
    """
    Render the right-column model information card used on the model details page
    (metadata and status only; no run action).
    """
    try:
        with container:
            with ui.card().classes('bg-zinc-50  border border-sky-300 p-6 sticky top-24'):
                ui.label('Model Information').classes('text-xl font-bold mb-4')

                # Version
                with ui.column().classes('gap-2 mb-4'):
                    ui.label('Version').classes('font-semibold')
                    ui.label(model_info.get('version', '') if isinstance(model_info, dict) else getattr(model_info, 'version', '')).classes('text-sm')

                # Author
                with ui.column().classes('gap-2 mb-4'):
                    ui.label('Developed By').classes('font-semibold')
                    ui.label(model_info.get('author', '') if isinstance(model_info, dict) else getattr(model_info, 'author', '')).classes('text-sm')

                # Last Updated
                updated_at = model_info_dict.get('updatedAt')
                cached_at = model_info_dict.get('cached_at')
                updated_str = 'N/A'
                if updated_at:
                    try:
                        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        updated_str = dt.strftime('%Y-%m-%d %H:%M:%S EDT')
                    except Exception:
                        updated_str = str(updated_at)
                elif cached_at:
                    try:
                        dt = datetime.fromisoformat(cached_at)
                        updated_str = dt.strftime('%Y-%m-%d %H:%M:%S EDT')
                    except Exception:
                        updated_str = 'N/A'

                with ui.column().classes('gap-2 mb-4'):
                    ui.label('Last Updated').classes('font-semibold')
                    ui.label(updated_str).classes('text-sm')

                # Server Status
                with ui.column().classes('gap-2 mb-4'):
                    ui.label('Status').classes('font-semibold')
                    status_color = 'text-green-600' if server_status == 'Online' else 'text-red-600'
                    ui.label(server_status).classes(f'text-sm font-semibold {status_color}')

                # GPU info
                gpu_required = model_info.gpu if model_info and hasattr(model_info, 'gpu') else model_info_dict.get('gpu', False)
                if gpu_required:
                    with ui.column().classes('gap-2 mb-4'):
                        ui.badge('GPU Required', color='red').classes('text-xs')
    except Exception as e:
        logger.exception("Error rendering model info card: %s", e)
        with container:
            ui.label(f'Error rendering model info: {e}').classes('text-red-600')

