"""
Image preview with bounding box overlay for batch result tables (e.g. age/gender).
"""

from __future__ import annotations

import ast
import logging
import os
from typing import Dict, List, Optional, Tuple

from nicegui import ui
from PIL import Image, ImageDraw

from frontend.components.results.results_utils import open_file, open_folder
from frontend.components.results.table_helpers import resolve_table_row_index

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

# Downscale large images before base64-encoding for the dialog (keeps payload small).
_MAX_PREVIEW_SIDE = 1600


def parse_int_bbox(value: object) -> Optional[Tuple[int, int, int, int]]:
    """Parse [x1, y1, x2, y2] from metadata string or sequence."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)) and len(value) == 4:
        try:
            t = tuple(int(round(float(x))) for x in value)
            if all(x >= 0 for x in t):
                return t  # type: ignore[return-value]
        except (TypeError, ValueError):
            return None
    s = str(value).strip()
    if not s:
        return None
    try:
        v = ast.literal_eval(s)
        if isinstance(v, (list, tuple)) and len(v) == 4:
            t = tuple(int(round(float(x))) for x in v)
            if all(x >= 0 for x in t):
                return t  # type: ignore[return-value]
    except (SyntaxError, ValueError, TypeError):
        pass
    return None


def _subtitle_for_row(row: Dict) -> str:
    title = str(row.get('title') or '').strip()
    gender = str(row.get('gender') or '').strip()
    age = str(row.get('age') or '').strip()
    meta_bits = [b for b in (gender, age) if b]
    if title and meta_bits:
        return f'{title} — {" ".join(meta_bits)}'
    if title:
        return title
    if meta_bits:
        return ' '.join(meta_bits)
    return ''


def _pil_image_with_bbox_drawn(
    source: Image.Image, bbox: Tuple[int, int, int, int]
) -> Image.Image:
    """Return an RGB image with a red rectangle (coordinates in source pixel space)."""
    x1, y1, x2, y2 = bbox
    im = source.convert('RGB')
    nw, nh = im.size
    x1 = max(0, min(nw - 1, x1))
    y1 = max(0, min(nh - 1, y1))
    x2 = max(x1 + 1, min(nw, x2))
    y2 = max(y1 + 1, min(nh, y2))

    m = max(nw, nh)
    if m > _MAX_PREVIEW_SIDE:
        scale = _MAX_PREVIEW_SIDE / m
        new_w = max(1, int(round(nw * scale)))
        new_h = max(1, int(round(nh * scale)))
        im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
        x1, y1, x2, y2 = (
            int(round(x1 * scale)),
            int(round(y1 * scale)),
            int(round(x2 * scale)),
            int(round(y2 * scale)),
        )
        x1 = max(0, min(new_w - 1, x1))
        y1 = max(0, min(new_h - 1, y1))
        x2 = max(x1 + 1, min(new_w, x2))
        y2 = max(y1 + 1, min(new_h, y2))

    draw = ImageDraw.Draw(im)
    draw.rectangle([x1, y1, x2, y2], outline='#ff0000', width=4)
    return im


def open_image_bbox_preview_dialog(abs_path: str, bbox: Tuple[int, int, int, int], row: Dict) -> None:
    x1, y1, x2, y2 = bbox
    if x2 <= x1 or y2 <= y1:
        open_file(abs_path)
        return
    try:
        with Image.open(abs_path) as im0:
            im0.load()
            preview = _pil_image_with_bbox_drawn(im0.copy(), bbox)
    except Exception as ex:
        logger.warning('Could not read image for bbox preview: %s', ex)
        open_file(abs_path)
        return

    heading = _subtitle_for_row(row) or os.path.basename(abs_path)
    parent_dir = os.path.dirname(abs_path)

    with ui.dialog() as dialog, ui.card().classes('max-w-5xl w-full'):
        ui.label(heading[:200]).classes('text-lg font-semibold')
        ui.image(preview).classes('max-w-full h-auto')
        ui.label(abs_path).classes('text-xs font-mono break-all text-gray-600')
        with ui.row().classes('gap-2 mt-2 flex-wrap'):
            if parent_dir:
                ui.button('Open folder', icon='folder_open', on_click=lambda d=parent_dir: open_folder(d)).props(
                    'outline'
                )
            ui.button('Close', on_click=dialog.close)
    dialog.open()


def create_bbox_preview_row_click_handler(rows: List[Dict], open_file_func):
    """
    Open a bbox overlay dialog for image rows with parsable ``bounding_box`` metadata;
    otherwise fall back to ``open_file_func``.
    """

    def on_row_click(e):
        try:
            row_index = resolve_table_row_index(e, rows)
            if row_index is None:
                return
            row = rows[row_index]
            file_path = row.get('path_full') or row.get('path')
            if not file_path:
                return
            if not os.path.isfile(file_path):
                open_file_func(file_path)
                return
            ext = os.path.splitext(file_path)[1].lower()
            bb = parse_int_bbox(row.get('bounding_box'))
            if bb and ext in _IMAGE_EXT:
                open_image_bbox_preview_dialog(file_path, bb, row)
            else:
                open_file_func(file_path)
        except Exception as ex:
            logger.warning('Error handling batch row click: %s', ex)

    return on_row_click
