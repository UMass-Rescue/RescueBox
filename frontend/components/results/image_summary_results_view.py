"""
Render image-summary job output: summary .txt paths plus input_dir so source images can be shown.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from nicegui import ui

from frontend.components.results.results_utils import open_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_IMAGE_SUFFIXES = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif')


def augment_response_model_dump_for_image_summary(
    model_dump: Dict[str, Any], job_fields: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Upgrade stored jobs that only have a JSON list of ``*.jpg.txt`` paths (no ``input_dir``)
    so the job page can show thumbnails using ``inputs.input_dir`` from the same job.
    """
    endpoint = (job_fields.get('endpoint') or '')
    if 'image_summary' not in endpoint:
        return model_dump
    root = model_dump.get('root')
    if not isinstance(root, dict) or root.get('output_type') != 'text':
        return model_dump
    val = root.get('value')
    if not isinstance(val, str):
        return model_dump
    try:
        parsed = json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return model_dump
    if isinstance(parsed, dict) and parsed.get('image_summary'):
        return model_dump
    if not isinstance(parsed, list) or not parsed or not all(isinstance(p, str) for p in parsed):
        return model_dump

    def looks_like_summary_txt(p: str) -> bool:
        name = Path(p).name
        if not name.endswith('.txt'):
            return False
        base = name[:-4]
        return any(base.lower().endswith(ext) for ext in _IMAGE_SUFFIXES)

    if not all(looks_like_summary_txt(p) for p in parsed):
        return model_dump

    req = job_fields.get('request') or {}
    inputs = req.get('inputs') if isinstance(req, dict) else {}
    if not isinstance(inputs, dict):
        return model_dump
    idir = inputs.get('input_dir') or {}
    path = idir.get('path') if isinstance(idir, dict) else None
    if not path:
        return model_dump

    out = dict(model_dump)
    out_root = dict(root)
    out_root['value'] = json.dumps(
        {
            'image_summary': True,
            'input_dir': str(Path(path).resolve()),
            'files': sorted(parsed),
        }
    )
    out['root'] = out_root
    return out


def source_image_path_from_summary(summary_txt_path: str, input_dir: str) -> Optional[str]:
    """
    Summary files are named like ``kid.jpg.txt`` under output_dir; the source image is
    ``input_dir/kid.jpg``.
    """
    name = Path(summary_txt_path).name
    if not name.endswith('.txt'):
        return None
    base = name[:-4]
    low = base.lower()
    if not any(low.endswith(ext) for ext in _IMAGE_SUFFIXES):
        return None
    candidate = str(Path(input_dir) / base)
    return candidate if os.path.isfile(candidate) else None


def render_image_summary_file_list(container: ui.element, payload: Dict[str, Any], title: str) -> None:
    """
    Searchable table-like layout with a thumbnail column for each summary row.
    """
    input_dir = str(payload.get('input_dir') or '')
    file_paths: List[str] = [p for p in (payload.get('files') or []) if isinstance(p, str)]

    file_data: List[Dict[str, Any]] = []
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                content = Path(file_path).read_text(encoding='utf-8')
                img = source_image_path_from_summary(file_path, input_dir) if input_dir else None
                file_data.append({
                    'path': file_path,
                    'filename': os.path.basename(file_path),
                    'content': content,
                    'content_lower': content.lower(),
                    'image_path': img,
                })
            else:
                logger.warning('File does not exist: %s', file_path)
        except Exception as e:
            logger.warning('Error reading file %s: %s', file_path, e)

    if not file_data:
        with container:
            ui.label('No files found or all files are empty').classes('text-red-600')
        return

    with container:
        with ui.card().classes('bg-green-50 border border-green-300 p-4'):
            with ui.column().classes('gap-2 w-full min-w-0'):
                ui.label(f'📝 {title} ({len(file_data)} files)').classes('font-bold')

                search_input = ui.input(
                    label='Search',
                    placeholder='Enter search term (e.g., "blue car")',
                    value='',
                ).classes('w-full').props('clearable')

                list_container = ui.column().classes('w-full min-w-0 gap-0')
                result_count_label = ui.label(
                    f'Showing {len(file_data)} of {len(file_data)} files'
                ).classes('text-xs text-gray-600')

                def render_rows(filtered: List[Dict[str, Any]]) -> None:
                    list_container.clear()
                    with list_container:
                        with ui.row().classes(
                            'w-full items-center gap-2 text-xs font-semibold text-gray-600 '
                            'border-b border-gray-200 pb-1 mb-1'
                        ):
                            ui.label('Image').classes('w-48 shrink-0 text-center')
                            ui.label('Summary file').classes('w-48 min-w-0 shrink-0')
                            ui.label('Description').classes('flex-grow min-w-0')
                        for file_info in filtered:
                            full_text = file_info['content']
                            path_full = file_info['path']
                            img_path = file_info.get('image_path')

                            def make_open(p: str):
                                return lambda: open_file(p)

                            with ui.row().classes(
                                'w-full items-start gap-2 py-2 border-b border-gray-100 '
                                'cursor-pointer hover:bg-white/80 rounded'
                            ).on('click', make_open(path_full)):
                                with ui.column().classes('w-48 shrink-0 items-center'):
                                    if img_path:
                                        ui.image(img_path).classes(
                                            'w-48 h-48 object-cover rounded border border-gray-200 shadow-sm'
                                        )
                                    else:
                                        ui.icon('image_not_supported', size='3rem').classes(
                                            'text-gray-400 mt-10'
                                        )
                                ui.label(file_info['filename']).classes(
                                    'w-48 min-w-0 shrink-0 text-xs font-mono break-all'
                                )
                                # Full summary text as markdown (model output is often plain prose; markdown still renders cleanly).
                                with ui.column().classes(
                                    'flex-grow min-w-0 max-h-[min(70vh,36rem)] overflow-y-auto '
                                    'pl-1 border-l border-gray-200'
                                ):
                                    ui.markdown(full_text or '_(empty)_').classes(
                                        'prose prose-sm max-w-none text-gray-800 leading-relaxed '
                                        'break-words [&_p]:my-1 [&_pre]:whitespace-pre-wrap'
                                    )

                def update_view(search_term: str = '') -> None:
                    search_lower = search_term.lower().strip()
                    if search_lower:
                        filtered = [f for f in file_data if search_lower in f['content_lower']]
                    else:
                        filtered = list(file_data)
                    render_rows(filtered)
                    result_count_label.text = f'Showing {len(filtered)} of {len(file_data)} files'

                update_view('')

                def on_search_change(e):
                    search_term = e.args if isinstance(e.args, str) else search_input.value
                    update_view(search_term)

                search_input.on('update:modelValue', on_search_change)
                search_input.on('blur', lambda: update_view(search_input.value))

                ui.label(
                    'Tip: Search filters by description text. Click a row to open the summary .txt file.'
                ).classes('text-xs text-gray-500 mt-1')
