"""Case management home (``/``) and active case overview (``/case``)."""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.components.shared import create_navbar
from frontend.pages.home_case_overview import render_active_case_overview
from frontend.pages.home_dashboard import render_case_management_cards
from frontend.pages.page_shell import COMPACT_TOOLBAR_HEAD_HTML
from frontend.utils import (
    apply_saved_theme,
    ensure_explicit_user_id_for_tests,
    get_active_case_id,
)

logger = logging.getLogger(__name__)

_CASE_PAGE_HEAD_HTML = COMPACT_TOOLBAR_HEAD_HTML


def _apply_case_page_shell() -> None:
    apply_saved_theme()
    ui.add_head_html(_CASE_PAGE_HEAD_HTML)
    create_navbar()
    ensure_explicit_user_id_for_tests()


@ui.page("/")
async def index():
    """Main dashboard / home page (Case Management Dashboard)."""
    logger.debug("Rendering main dashboard page (index route)")
    _apply_case_page_shell()

    with ui.column().classes(
        "container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16 gap-8"
    ):
        with ui.row().classes("w-full items-center gap-3 mb-2"):
            ui.label("RescueBox Case Management").classes(
                "text-4xl font-bold text-slate-800"
            )
        ui.label(
            "Create a new investigative case or load an existing one to begin."
        ).classes("text-lg text-slate-500 mb-8 pl-1")

        await render_case_management_cards()

    logger.debug("Main dashboard page rendered successfully")


@ui.page("/case")
async def case_overview():
    """Active Case Overview / Dashboard."""
    logger.debug("Rendering case overview page")
    _apply_case_page_shell()

    active_case_id = get_active_case_id()

    if not active_case_id:
        ui.notify(
            "No active case loaded. Please create or load a case.", type="warning"
        )
        ui.timer(0.1, _navigate_home, once=True)
        return

    await render_active_case_overview(active_case_id)


def _navigate_home() -> None:
    ui.navigate.to("/")

    logger.debug("Case overview page rendered successfully")
