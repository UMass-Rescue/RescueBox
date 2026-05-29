"""
Read-only explorer for the demo sample directory (e.g. Documents/demo) on the /demo page
and on individual walkthrough pages (filtered to folders relevant to each guide).
Paths are constrained to DEMO_FILES_BROWSE_ROOT to avoid directory traversal.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import FrozenSet, List, Optional, Tuple

from nicegui import ui

from frontend.config import DEMO_FILES_BROWSE_ROOT
from frontend.components.results.results_utils import open_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class _WalkthroughPreset:
    """Per-walkthrough browsing: optional start folder under demo root, filters on top-level listing."""

    __slots__ = ('initial_subpath', 'include_top_level', 'exclude_dirs')

    def __init__(
        self,
        initial_subpath: Optional[str] = None,
        include_top_level: Optional[FrozenSet[str]] = None,
        exclude_dirs: Optional[FrozenSet[str]] = None,
    ) -> None:
        self.initial_subpath = initial_subpath
        self.include_top_level = include_top_level
        self.exclude_dirs = exclude_dirs


# Presets aligned with frontend/demo/*.md walkthroughs.
_WALKTHROUGH_PRESETS: dict[str, _WalkthroughPreset] = {
    # transcribe_walkthrough.md — show transcribe-audio at demo root (do not start inside it, or only "inputs" shows)
    'transcribe': _WalkthroughPreset(
        include_top_level=frozenset({'transcribe-audio'}),
    ),
    # image_search_walkthrough.md — search-images only
    'image_search': _WalkthroughPreset(
        include_top_level=frozenset({'search-images'}),
    ),
    # other_walkthrough.md — only age-gender-classifier and describe-images at demo root
    'other': _WalkthroughPreset(
        include_top_level=frozenset({'age-gender-classifier', 'describe-images'}),
    ),
    # quick_start.md — full demo tree
    'quick_start': _WalkthroughPreset(),
    # Main /demo index — unfiltered
    'all': _WalkthroughPreset(),
}


def normalize_demo_walkthrough_query(value: Optional[str]) -> str:
    """
    Map a URL query value (e.g. ``?walkthrough=transcribe``) to a preset key for
    :func:`render_demo_files_explorer` / :func:`render_walkthrough_samples_panel`.
    Unknown or empty values become ``'all'`` (full demo tree).
    """
    if value is None or not str(value).strip():
        return 'all'
    k = str(value).strip().lower().replace('-', '_')
    if k in _WALKTHROUGH_PRESETS:
        return k
    return 'all'


def _resolved_root() -> Path:
    return DEMO_FILES_BROWSE_ROOT.expanduser().resolve()


def _is_under_root(path: Path, root: Path) -> bool:
    try:
        path = path.resolve()
        path.relative_to(root)
        return True
    except (ValueError, OSError, RuntimeError):
        return False


def _name_set(names: Optional[FrozenSet[str]]) -> Optional[set[str]]:
    if not names:
        return None
    return {n.lower() for n in names}


def _list_entries(
    directory: Path,
    *,
    list_root: Path,
    include_top_level: Optional[FrozenSet[str]],
    exclude_dirs: Optional[FrozenSet[str]],
) -> List[Tuple[Path, bool]]:
    """Sorted list of (path, is_dir). Filters apply to directory entries only."""
    try:
        entries = list(directory.iterdir())
    except OSError as e:
        logger.warning('Cannot list %s: %s', directory, e)
        return []
    dirs = sorted((p for p in entries if p.is_dir()), key=lambda p: p.name.lower())
    files = sorted((p for p in entries if p.is_file()), key=lambda p: p.name.lower())

    excl = _name_set(exclude_dirs)
    if excl:
        dirs = [p for p in dirs if p.name.lower() not in excl]

    try:
        at_root = directory.resolve() == list_root.resolve()
    except OSError:
        at_root = False

    incl = _name_set(include_top_level)
    if incl is not None and at_root:
        dirs = [p for p in dirs if p.name.lower() in incl]

    return [(p, True) for p in dirs] + [(p, False) for p in files]


def render_demo_files_explorer(
    container: ui.element,
    *,
    walkthrough: Optional[str] = 'all',
) -> None:
    """
    Render breadcrumb-style navigation and a clickable file/folder list.

    Args:
        walkthrough: Preset name — 'all' (default, full tree), 'transcribe', 'image_search',
            'other', 'quick_start'. Unknown values fall back to 'all'.
    """
    root = _resolved_root()
    key = walkthrough if walkthrough in _WALKTHROUGH_PRESETS else 'all'
    preset = _WALKTHROUGH_PRESETS[key]

    include_top = preset.include_top_level
    exclude_dirs = preset.exclude_dirs

    initial = root
    if preset.initial_subpath:
        candidate = root / preset.initial_subpath
        if candidate.is_dir():
            initial = candidate
        elif include_top is not None:
            # Stay at root; only show allowed top-level folder(s), e.g. transcribe-audio
            pass
        else:
            initial = root

    with container:
        if not root.exists() or not root.is_dir():
            ui.label(f'Demo files folder is not available: {root}').classes(
                'text-zinc-900 bg-[#a2aaad]/15 border border-[#a2aaad] rounded-lg p-4'
            )
            ui.label(
                'Create it or set RESCUEBOX_DEMO_FILES_DIR to an existing directory.'
            ).classes('text-sm text-zinc-600 mt-2')
            return

        state = {'current': str(initial)}

        list_holder = ui.column().classes('w-full min-w-0 gap-1')

        def go_to(new_path: str) -> None:
            target = Path(new_path).resolve()
            if not _is_under_root(target, root):
                ui.notify('Invalid path', type='negative', classes='rb-notify-505759')
                return
            if not target.is_dir():
                ui.notify('Not a folder', type='negative', classes='rb-notify-505759')
                return
            state['current'] = str(target)
            refresh()

        def refresh() -> None:
            list_holder.clear()
            cur = Path(state['current'])
            if not _is_under_root(cur, root):
                state['current'] = str(initial)
                cur = initial
            if not cur.is_dir():
                ui.notify('Invalid folder', type='negative', classes='rb-notify-505759')
                state['current'] = str(initial)
                cur = initial

            with list_holder:
                nav = ui.row().classes('w-full items-center gap-2 flex-wrap mb-2')
                with nav:
                    ui.button(
                        'Demo root',
                        on_click=lambda: go_to(str(root)),
                    ).classes('text-xs').props('dense outline')
                    if cur != root:
                        parent = cur.parent
                        if parent == root or _is_under_root(parent, root):
                            ui.button(
                                'Up one level',
                                on_click=lambda p=str(parent): go_to(p),
                            ).classes('text-xs').props('dense outline')

                for path, is_dir in _list_entries(
                    cur,
                    list_root=root,
                    include_top_level=include_top,
                    exclude_dirs=exclude_dirs,
                ):
                    name = path.name
                    if name.startswith('.'):
                        continue

                    row = ui.row().classes(
                        'w-full min-w-0 items-center gap-2 py-2 px-2 rounded '
                        'hover:bg-zinc-100 cursor-pointer border border-zinc-100'
                    )
                    if is_dir:
                        row.on('click', lambda *a, d=str(path): go_to(d))
                        with row:
                            ui.icon('folder', size='sm').classes('text-yellow-500 shrink-0')
                            ui.label(name).classes('text-sm font-medium text-zinc-900 truncate flex-1 min-w-0')
                            ui.icon('arrow_forward', size='sm').classes('text-zinc-400 shrink-0')
                    else:
                        row.on('click', lambda *a, f=str(path): open_file(f))
                        with row:
                            ui.icon('insert_drive_file', size='sm').classes('text-[#a2aaad] shrink-0')
                            ui.label(name).classes('text-sm text-zinc-800 truncate flex-1 min-w-0')

        refresh()


def render_walkthrough_samples_panel(container: ui.element, walkthrough: str) -> None:
    """Section with title + filtered explorer for a walkthrough page."""
    with container:
        with ui.column().props('id=walkthrough-samples').classes('w-full scroll-mt-24 mt-6'):
            ui.label('Sample inputs & outputs').classes('text-xl font-bold mb-1')
            ui.label(
                'Browse folders and files for this demo. '
            ).classes('text-sm text-zinc-600 mb-3')
            with ui.card().classes('w-full p-4 bg-zinc-50 border border-zinc-200 rounded-lg'):
                render_demo_files_explorer(
                    ui.column().classes('w-full min-w-0'),
                    walkthrough=walkthrough,
                )
