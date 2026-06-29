"""Shared layout for in-app demo walkthrough pages."""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.demo import (
    load_markdown_file,
    render_guided_markdown_body,
    schedule_hash_fragment_scroll,
)
from frontend.components.shared import create_navbar
from frontend.constants import NAV_LINKS
from frontend.utils.ui import apply_saved_theme, require_demo_user_session

logger = logging.getLogger(__name__)


def format_demo_shortcuts(*links: tuple[str, str]) -> str:
    """Markdown line of demo navigation shortcuts."""
    joined = " · ".join(f"[{label}]({url})" for label, url in links)
    return f"**Shortcuts:** {joined}\n"


def missing_walkthrough_markdown(
    md_file: str, shortcut_links: tuple[tuple[str, str], ...]
) -> str:
    """Fallback body when a demo markdown file is missing."""
    shortcuts = format_demo_shortcuts(*shortcut_links)
    return f"""## Missing walkthrough file

Could not read `{md_file}`. Add `frontend/demo/{md_file}` to customize this page.

{shortcuts}
"""


_WALKTHROUGH_COLUMN = "container mx-auto px-4 sm:px-8 py-8 w-full max-w-4xl pb-16"
_DEMO_BACK_BTN = (
    "bg-slate-100 hover:bg-slate-200 text-slate-800 px-4 py-2 rounded-lg "
    "font-medium transition-colors border border-slate-200"
)
_TITLE_CLS = "text-4xl font-bold text-slate-800"


def register_demo_walkthrough_route(
    route: str,
    md_file: str,
    shortcuts: tuple[tuple[str, str], ...],
    *,
    icon: str,
    title: str,
    log_label: str,
    extra_footer_links: list[tuple[str, str]] | None = None,
):
    """Register a NiceGUI demo walkthrough page with shared layout."""

    @ui.page(route)
    async def _walkthrough_page():
        if not begin_demo_walkthrough_page():
            return

        text = load_markdown_file(
            md_file, lambda: missing_walkthrough_markdown(md_file, shortcuts)
        )
        render_demo_walkthrough_content(
            icon=icon,
            title=title,
            markdown_body=text,
            log_label=log_label,
            extra_footer_links=extra_footer_links,
        )

    return _walkthrough_page


def begin_demo_walkthrough_page() -> bool:
    """Apply theme, navbar, and demo user gate. Returns False if the page should stop."""
    apply_saved_theme()
    create_navbar()
    return require_demo_user_session()


def render_demo_walkthrough_content(
    *,
    icon: str,
    title: str,
    markdown_body: str,
    log_label: str,
    extra_footer_links: list[tuple[str, str]] | None = None,
) -> None:
    """Standard walkthrough column: title, markdown body, back link."""
    with ui.column().classes(_WALKTHROUGH_COLUMN):
        with ui.row().classes("items-center gap-2 mb-2"):
            ui.icon(icon, size="lg").classes("text-[#881c1c]")
            ui.label(title).classes(_TITLE_CLS)

        render_guided_markdown_body(
            ui.column().classes("w-full min-w-0"), markdown_body
        )

        with ui.row().classes("gap-4 flex-wrap items-center mt-8"):
            ui.button(
                "Back to Demo",
                icon="arrow_back",
                on_click=lambda: ui.navigate.to(NAV_LINKS["demo"]),
            ).classes(_DEMO_BACK_BTN)
            for label, href in extra_footer_links or []:
                ui.link(label, href).classes(
                    "text-[#881c1c] hover:underline font-medium"
                )

    schedule_hash_fragment_scroll()
    logger.debug("%s walkthrough page rendered", log_label)
