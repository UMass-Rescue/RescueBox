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
from frontend.design_tokens import Design

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_IMAGE_SUFFIXES = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.gif')

# Global body { font-size: 0.8rem !important } in some pages shrinks all UI; override inside this dialog only.
_IMAGE_SUMMARY_MODAL_CSS_DONE = False


def _ensure_image_summary_modal_css() -> None:
    global _IMAGE_SUMMARY_MODAL_CSS_DONE
    if _IMAGE_SUMMARY_MODAL_CSS_DONE:
        return
    _IMAGE_SUMMARY_MODAL_CSS_DONE = True
    ui.add_head_html(
        '''
        <style>
        /* Right-docked summary panel: keep left side (thumbnails) visible; lighter dim */
        .q-dialog.image-summary-side-dialog .q-dialog__backdrop {
            opacity: 0.35 !important;
        }
        /* Beat body !important and Quasar markdown defaults for readability */
        .image-summary-md-modal,
        .image-summary-md-modal .q-markdown,
        .image-summary-md-modal p,
        .image-summary-md-modal li,
        .image-summary-md-modal ul,
        .image-summary-md-modal ol {
            font-size: 1.25rem !important;
            line-height: 1.75 !important;
        }
        .image-summary-md-modal h1 { font-size: 1.875rem !important; }
        .image-summary-md-modal h2 { font-size: 1.5rem !important; }
        .image-summary-md-modal h3 { font-size: 1.25rem !important; }
        .image-summary-md-modal pre,
        .image-summary-md-modal code {
            font-size: 1rem !important;
            line-height: 1.5 !important;
        }
        /* Job results — image summarize search box (Medium Gray #505759, not primary maroon) */
        .rb-image-summary-search-field.q-field--outlined .q-field__control:before {
            border-color: #505759 !important;
        }
        .rb-image-summary-search-field.q-field--outlined:hover .q-field__control:before {
            border-color: #505759 !important;
        }
        .rb-image-summary-search-field.q-field--focused .q-field__control:before {
            border-color: #505759 !important;
        }
        .rb-image-summary-search-field .q-field__label,
        .rb-image-summary-search-field.q-field--float .q-field__label {
            color: #505759 !important;
        }
        .rb-image-summary-search-field .q-field__marginal .q-icon,
        .rb-image-summary-search-field .q-field__append .q-icon {
            color: #505759 !important;
        }
        </style>
        ''',
        shared=True,
    )

# Markdown body sizing: do not rely on `prose` alone (typography plugin may be absent; Quasar can keep small inner text).
# Use !text-* so Quasar / dialog defaults cannot override paragraph size.
_MD_MODAL = (
    'max-w-none text-zinc-900 '
    '[&_p]:!text-xl [&_p]:!leading-relaxed [&_p]:my-3 '
    '[&_li]:!text-xl [&_li]:!leading-relaxed [&_ul]:my-3 [&_ol]:my-3 '
    '[&_blockquote]:!text-lg [&_blockquote]:border-l-4 [&_blockquote]:pl-4 '
    '[&_pre]:!text-base [&_pre]:leading-relaxed [&_pre]:whitespace-pre-wrap [&_pre]:p-3 [&_pre]:bg-zinc-100 [&_pre]:rounded '
    '[&_code]:!text-base [&_h1]:!text-3xl [&_h2]:!text-2xl [&_h3]:!text-xl '
    '[&_strong]:font-semibold [&_div]:!text-xl'
)
_MD_INLINE = (
    'max-w-none text-zinc-800 '
    '[&_p]:text-base [&_p]:leading-relaxed [&_p]:my-2 '
    '[&_li]:text-base [&_li]:leading-relaxed '
    '[&_pre]:text-sm [&_pre]:whitespace-pre-wrap [&_code]:text-sm'
)


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


def _open_source_image(image_path: str) -> None:
    """Open the source image via the shared viewer (served URL / system handler)."""
    if not image_path or not os.path.isfile(image_path):
        ui.notify('Image file is not available on disk.', type='warning', classes='rb-notify-505759')
        return
    open_file(image_path)


def _open_image_summary_markdown_modal(file_info: Dict[str, Any]) -> None:
    """Full summary in a right-docked panel so thumbnails on the left stay visible beside it."""
    _ensure_image_summary_modal_css()
    txt = file_info.get('content') or ''
    name = file_info.get('filename') or 'Summary'
    path_full = file_info.get('path') or ''
    with ui.dialog() as dialog:
        dialog.props('position=right full-height')
        dialog.classes('image-summary-side-dialog')
        dialog.style('width: min(520px, 48vw); max-width: 100vw;')
        with ui.card().classes(
            'w-full h-full min-h-0 flex flex-col p-6 rounded-none shadow-2xl '
            'border-l border-zinc-200 bg-white'
        ):
            ui.label(name).classes('text-2xl font-semibold shrink-0 mb-4')
            with ui.column().classes(
                'overflow-y-auto flex-1 min-h-0 w-full image-summary-md-modal'
            ).style('font-size: 1.25rem; line-height: 1.75;'):
                ui.markdown(txt or '_(empty)_').classes(_MD_MODAL)
            with ui.row().classes('gap-2 mt-4 shrink-0 justify-end flex-wrap'):
                if path_full:
                    ui.button('Open raw file', on_click=lambda p=path_full: open_file(p)).props('flat outline')
                ui.button('Close', on_click=dialog.close).classes(Design.BTN_MEDIUM_GRAY)
    dialog.open()


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

    Prefer ``file_pairs`` (``input_path`` / ``output_path``) from the plugin when present;
    otherwise fall back to ``input_dir`` + filename heuristic.
    """
    input_dir = str(payload.get('input_dir') or '')
    file_paths: List[str] = [p for p in (payload.get('files') or []) if isinstance(p, str)]
    out_to_in: Dict[str, str] = {}
    raw_pairs = payload.get('file_pairs')
    if isinstance(raw_pairs, list):
        for pr in raw_pairs:
            if not isinstance(pr, dict):
                continue
            op = pr.get('output_path')
            ip = pr.get('input_path')
            if isinstance(op, str) and isinstance(ip, str) and op.strip():
                out_to_in[op] = ip

    file_data: List[Dict[str, Any]] = []
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                content = Path(file_path).read_text(encoding='utf-8')
                img = out_to_in.get(file_path)
                if not img and input_dir:
                    img = source_image_path_from_summary(file_path, input_dir)
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
            ui.label('No valid files found').classes('text-red-600')
        return

    _ensure_image_summary_modal_css()

    with container:
        summary_shell = ui.card().classes('w-full p-4')
        with summary_shell:
            with ui.column().classes('gap-2 w-full min-w-0'):
                ui.label(f'{title} ({len(file_data)} files)').classes(
                    'text-lg font-bold text-zinc-900'
                )

                with ui.element('div').classes(
                    'w-full rounded-lg border-2 border-[#505759] bg-white p-3 shadow-sm'
                ):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('search', size='1.5rem').classes('text-[#505759] shrink-0')
                        ui.label('Search').classes(
                            'text-lg font-bold text-[#505759] tracking-tight'
                        )
                    search_input = ui.input(
                        placeholder='Type to filter rows by description (e.g. blue car)',
                        value='',
                    ).classes('w-full rb-image-summary-search-field').props(
                        'clearable outlined dense'
                    )

                list_container = ui.column().classes('w-full min-w-0 gap-0')
                result_count_label = ui.label(
                    f'Showing {len(file_data)} of {len(file_data)} files'
                ).classes('text-sm text-zinc-600')

                def render_rows(filtered: List[Dict[str, Any]]) -> None:
                    list_container.clear()
                    with list_container:
                        # Same 3-column grid as data rows so headers align; narrow viewports scroll horizontally.
                        with ui.element('div').classes('w-full min-w-0 overflow-x-auto'):
                            with ui.element('div').classes(
                                'grid min-w-[720px] w-full grid-cols-[12rem_minmax(0,1fr)] '
                                'gap-3 items-center pb-1 mb-1 border-b border-zinc-200 text-xs font-semibold text-zinc-600'
                            ):
                                ui.label('Image').classes('text-center')
                                with ui.element('div').classes(
                                    'min-w-0 grid grid-cols-[12rem_minmax(0,1fr)] gap-3 items-center'
                                ):
                                    ui.label('Summary file').classes('min-w-0')
                                    ui.label('Description').classes('min-w-0')
                        for file_info in filtered:
                            full_text = file_info['content']
                            fi_snapshot = dict(file_info)
                            img_path = file_info.get('image_path') or ''

                            with ui.element('div').classes('w-full min-w-0 overflow-x-auto'):
                                with ui.element('div').classes(
                                    'grid min-w-[720px] w-full grid-cols-[12rem_minmax(0,1fr)] '
                                    'gap-3 items-start py-2 border-b border-zinc-100 rounded'
                                ):
                                    with ui.column().classes(
                                        'w-48 shrink-0 items-center justify-start gap-1'
                                    ):
                                        if img_path:
                                            ui.image(img_path).classes(
                                                'w-48 h-48 object-cover rounded border border-zinc-200 '
                                                'shadow-sm cursor-pointer hover:ring-2 hover:ring-[#505759] '
                                                'transition-shadow'
                                            ).on('click', lambda p=img_path: _open_source_image(p))
                                            ui.label('Click image to open').classes(
                                                'text-[10px] uppercase tracking-wide text-zinc-500'
                                            )
                                        else:
                                            ui.icon('image_not_supported', size='3rem').classes(
                                                'text-zinc-400 mt-10'
                                            )
                                    with ui.element('div').classes(
                                        'min-w-0 grid grid-cols-[12rem_minmax(0,1fr)] gap-3 items-start '
                                        'cursor-pointer hover:bg-white/80 rounded p-1 -m-1'
                                    ).on(
                                        'click',
                                        lambda fi=fi_snapshot: _open_image_summary_markdown_modal(fi),
                                    ):
                                        ui.label(file_info['filename']).classes(
                                            'min-w-0 text-sm font-mono break-all self-start pt-1'
                                        )
                                        with ui.column().classes(
                                            'min-w-0 border-l border-zinc-200 pl-2 max-h-56 overflow-y-auto'
                                        ):
                                            ui.markdown(full_text or '_(empty)_').classes(_MD_INLINE)

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
                    'Tip: Search the description text. Click the image to open it in the viewer; '
                    'click the summary file or description for the full text summary.'
                ).classes('text-sm text-zinc-500 mt-1')
