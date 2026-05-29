import logging
from nicegui import ui
from typing import List, Dict, Any, Callable
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_file_grid(container: ui.element, grouped_files: Dict[str, List[Any]], open_handler: Callable[[str], None]) -> None:
    """
    Render files grouped by type in expandable expansions with grid thumbnails/buttons.
    """
    try:
        with container:
            for file_type, files in grouped_files.items():
                with ui.expansion(f'{file_type.upper()} ({len(files)})', icon='folder').classes('w-full'):
                    with ui.grid(columns=3).classes('gap-2 mt-2'):
                        for file_info in files[:20]:
                            file_path = getattr(file_info, 'path', file_info.get('path') if isinstance(file_info, dict) else str(file_info))
                            if file_type in ['img', 'image']:
                                ui.image(file_path).classes('w-full h-32 object-cover cursor-pointer').on('click', lambda e, p=file_path: open_handler(p))
                            else:
                                ui.button(
                                    os.path.basename(file_path),
                                    on_click=lambda path=file_path: open_handler(path)
                                ).classes('text-xs truncate text-indigo-600 hover:underline').props('flat')
    except Exception as e:
        logger.exception("Error rendering file grid: %s", e)
        with container:
            ui.label(f'Error rendering grid: {e}').classes('text-red-600')

