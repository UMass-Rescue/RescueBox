"""Read-only explorer for demo sample files on /demo and walkthrough pages.

Also includes shared Markdown rendering for in-app guides; screenshot placeholders
``{{SCREENSHOT:filename.png}}`` load from ``/demo-media/<filename>`` (under ``frontend/demo/``).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

from nicegui import ui

from frontend.components.results import open_file
from frontend.config import DEMO_FILES_BROWSE_ROOT
from frontend.constants import DEMO_WALKTHROUGH_MEDIA_URL

_DEMO_NAV_BTN = (
    "text-xs bg-slate-100 hover:bg-slate-200 text-slate-800 px-2 py-1 rounded "
    "border border-slate-200 transition-colors"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class WalkthroughPreset(NamedTuple):
    """Per-walkthrough browsing: start folder and top-level filters under demo root."""

    initial_subpath: str | None = None
    include_top_level: frozenset[str] | None = None
    exclude_dirs: frozenset[str] | None = None


# Presets aligned with frontend/demo/*.md walkthroughs.
_WALKTHROUGH_PRESETS: dict[str, WalkthroughPreset] = {
    # transcribe_walkthrough.md — show transcribe-audio at demo root (do not start inside it, or only "inputs" shows)
    "transcribe": WalkthroughPreset(
        include_top_level=frozenset({"transcribe-audio"}),
    ),
    # image_search_walkthrough.md — search-images only
    "image_search": WalkthroughPreset(
        include_top_level=frozenset({"search-images"}),
    ),
    # other_walkthrough.md — only age-gender-classifier and describe-images at demo root
    "other": WalkthroughPreset(
        include_top_level=frozenset({"age-gender-classifier", "describe-images"}),
    ),
    # quick_start.md — full demo tree
    "quick_start": WalkthroughPreset(),
    # Main /demo index — unfiltered
    "all": WalkthroughPreset(),
}


def normalize_demo_walkthrough_query(value: str | None) -> str:
    """
    Map a URL query value (e.g. ``?walkthrough=transcribe``) to a preset key for
    :func:`render_demo_files_explorer` / :func:`render_walkthrough_samples_panel`.
    Unknown or empty values become ``'all'`` (full demo tree).
    """
    if value is None or not str(value).strip():
        return "all"
    k = str(value).strip().lower().replace("-", "_")
    if k in _WALKTHROUGH_PRESETS:
        return k
    return "all"


def _resolved_root() -> Path:
    return DEMO_FILES_BROWSE_ROOT.expanduser().absolute()


def _is_under_root(path: Path, root: Path) -> bool:
    try:
        path = path.absolute()
        path.relative_to(root)
        return True
    except (ValueError, OSError, RuntimeError):
        return False


def _name_set(names: frozenset[str] | None) -> set[str] | None:
    if not names:
        return None
    return {n.lower() for n in names}


def _list_entries(
    directory: Path,
    *,
    list_root: Path,
    include_top_level: frozenset[str] | None,
    exclude_dirs: frozenset[str] | None,
) -> list[tuple[Path, bool]]:
    """Sorted list of (path, is_dir). Filters apply to directory entries only."""
    try:
        entries = list(directory.iterdir())
    except OSError as e:
        logger.warning("Cannot list %s: %s", directory, e)
        return []
    dirs = sorted((p for p in entries if p.is_dir()), key=lambda p: p.name.lower())
    files = sorted((p for p in entries if p.is_file()), key=lambda p: p.name.lower())

    excl = _name_set(exclude_dirs)
    if excl:
        dirs = [p for p in dirs if p.name.lower() not in excl]

    try:
        at_root = directory.absolute() == list_root.absolute()
    except OSError:
        at_root = False

    incl = _name_set(include_top_level)
    if incl is not None and at_root:
        dirs = [p for p in dirs if p.name.lower() in incl]

    return [(p, True) for p in dirs] + [(p, False) for p in files]


def render_demo_files_explorer(
    container: ui.element,
    *,
    walkthrough: str | None = "all",
) -> None:
    """
    Render breadcrumb-style navigation and a clickable file/folder list.

    Args:
        walkthrough: Preset name — 'all' (default, full tree), 'transcribe', 'image_search',
            'other', 'quick_start'. Unknown values fall back to 'all'.
    """
    root = _resolved_root()
    key = walkthrough if walkthrough in _WALKTHROUGH_PRESETS else "all"
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
            ui.label(f"Demo files folder is not available: {root}").classes(
                "text-zinc-900 bg-[#a2aaad]/15 border border-[#a2aaad] rounded-lg p-4"
            )
            ui.label(
                "Create the folder, clone sample data into it, or set "
                "RESCUEBOX_DEMO_FILES_DIR to an existing directory "
                "(dev checkout: src-tauri/demo)."
            ).classes("text-sm text-zinc-600 mt-2")
            return

        state = {"current": str(initial)}

        list_holder = ui.column().classes("w-full min-w-0 gap-1")

        def go_to(new_path: str) -> None:
            target = Path(new_path).absolute()
            if not _is_under_root(target, root):
                ui.notify("Invalid path", type="negative", classes="rb-notify-505759")
                return
            if not target.is_dir():
                ui.notify("Not a folder", type="negative", classes="rb-notify-505759")
                return
            state["current"] = str(target)
            refresh()

        def refresh() -> None:
            list_holder.clear()
            cur = Path(state["current"])
            if not _is_under_root(cur, root):
                state["current"] = str(initial)
                cur = initial
            if not cur.is_dir():
                ui.notify("Invalid folder", type="negative", classes="rb-notify-505759")
                state["current"] = str(initial)
                cur = initial

            with list_holder:
                nav = ui.row().classes("w-full items-center gap-2 flex-wrap mb-2")
                with nav:
                    ui.button(
                        "Demo root",
                        color=None,
                        on_click=lambda: go_to(str(root)),
                    ).classes(_DEMO_NAV_BTN).props("dense")
                    if cur != root:
                        parent = cur.parent
                        if parent == root or _is_under_root(parent, root):
                            ui.button(
                                "Up one level",
                                color=None,
                                on_click=lambda: go_to(str(parent)),
                            ).classes(_DEMO_NAV_BTN).props("dense")

                for path, is_dir in _list_entries(
                    cur,
                    list_root=root,
                    include_top_level=include_top,
                    exclude_dirs=exclude_dirs,
                ):
                    name = path.name
                    if name.startswith("."):
                        continue

                    row = ui.row().classes(
                        "w-full min-w-0 items-center gap-2 py-2 px-2 rounded "
                        "hover:bg-zinc-100 cursor-pointer border border-zinc-100"
                    )
                    if is_dir:
                        row.on("click", lambda *a, d=str(path): go_to(d))
                        with row:
                            ui.icon("folder", size="sm").classes(
                                "text-yellow-500 shrink-0"
                            )
                            ui.label(name).classes(
                                "text-sm font-medium text-zinc-900 truncate flex-1 min-w-0"
                            )
                            ui.icon("arrow_forward", size="sm").classes(
                                "text-zinc-400 shrink-0"
                            )
                    else:
                        row.on("click", lambda *a, f=str(path): open_file(f))
                        with row:
                            ui.label(name).classes(
                                "text-sm text-zinc-800 truncate flex-1 min-w-0"
                            )

        refresh()


def render_walkthrough_samples_panel(container: ui.element, walkthrough: str) -> None:
    """Section with title + filtered explorer for a walkthrough page."""
    with container, ui.column().props("id=walkthrough-samples").classes(
        "w-full scroll-mt-24 mt-6"
    ):
        ui.label("Sample inputs & outputs").classes("text-xl font-bold mb-1")
        ui.label("Browse folders and files for this demo. ").classes(
            "text-sm text-zinc-600 mb-3"
        )
        with ui.card().classes(
            "w-full p-4 bg-zinc-50 border border-zinc-200 rounded-lg"
        ):
            render_demo_files_explorer(
                ui.column().classes("w-full min-w-0"),
                walkthrough=walkthrough,
            )


_FRONTEND_DEMO_DIR = Path(__file__).absolute().parent.parent / "demo"


def schedule_hash_fragment_scroll() -> None:
    """
    Scroll to the element whose id matches the URL fragment (e.g. /demo#sample-inputs,
    /demo/transcribe-walkthrough#walkthrough-samples). NiceGUI client-side navigation
    often does not perform native hash scrolling; this runs after paint.
    """
    js = """
        (function () {
            var id = (window.location.hash || '').replace(/^#/, '');
            if (!id) return;
            function tryScroll() {
                var el = document.getElementById(id);
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    return true;
                }
                return false;
            }
            if (!tryScroll()) {
                setTimeout(function () { tryScroll(); }, 200);
                setTimeout(function () { tryScroll(); }, 600);
            }
        })();
    """
    ui.timer(0.15, lambda: ui.run_javascript(js), once=True)
    ui.timer(0.5, lambda: ui.run_javascript(js), once=True)


_SCREENSHOT_LINE = re.compile(r"^\{\{SCREENSHOT:([^}]+)\}\}\s*$", re.MULTILINE)


def strip_editor_comment(text: str) -> str:
    return re.sub(r"^\s*<!--.*?-->\s*", "", text, count=1, flags=re.DOTALL)


def load_markdown_file(relative_name: str, fallback: Callable[[], str]) -> str:
    """Load ``frontend/demo/<relative_name>`` or use fallback."""
    path = _FRONTEND_DEMO_DIR / relative_name
    if path.is_file():
        try:
            return strip_editor_comment(path.read_text(encoding="utf-8"))
        except OSError as e:
            logger.warning("Could not read %s: %s", path, e)
    return fallback()


def iter_md_and_images(text: str):
    """Split markdown on {{SCREENSHOT:file.png}} lines; yield ('md', str) or ('img', filename)."""
    pos = 0
    matches = list(_SCREENSHOT_LINE.finditer(text))
    if not matches:
        # No screenshot directives: single markdown segment only (avoid duplicating full body)
        if text.strip():
            yield ("md", text.strip())
        return

    for m in matches:
        if m.start() > pos:
            chunk = text[pos : m.start()].strip()
            if chunk:
                yield ("md", chunk)
        yield ("img", m.group(1).strip())
        pos = m.end()
    if pos < len(text):
        tail = text[pos:].strip()
        if tail:
            yield ("md", tail)


def render_guided_markdown_body(
    container: ui.element,
    markdown_text: str,
    *,
    image_base_url: str = DEMO_WALKTHROUGH_MEDIA_URL,
) -> None:
    """Render markdown; ``{{SCREENSHOT:file.png}}`` lines load images from ``<image_base_url>/file.png``."""
    base = image_base_url.rstrip("/") or DEMO_WALKTHROUGH_MEDIA_URL
    segments = list(iter_md_and_images(markdown_text))
    if not segments:
        ui.label("Guide content is empty.").classes("text-zinc-500")
        return
    with container:
        for kind, payload in segments:
            if kind == "md":
                # Tailwind text-* on the element; use ! so global body { font-size: 0.8rem !important } does not win.
                ui.markdown(payload).classes(
                    "prose prose-zinc max-w-none "
                    "!text-xl leading-relaxed "
                    "[&_p]:!text-xl [&_li]:!text-xl "
                    "[&_h1]:!text-3xl [&_h2]:!text-2xl [&_h3]:!text-2xl"
                )
            else:
                safe = Path(payload).name
                if (
                    safe != payload
                    or ".." in payload
                    or "/" in payload
                    or "\\" in payload
                ):
                    logger.warning("Ignoring unsafe screenshot name: %s", payload)
                    continue
                ui.image(f"{base}/{safe}").classes(
                    "w-full max-w-3xl rounded-lg border border-zinc-200 shadow-md my-4"
                )
