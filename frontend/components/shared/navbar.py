"""Main application navigation bar."""

from __future__ import annotations

from nicegui import ui

from frontend import constants
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.database import get_case_db
from frontend.design_tokens import Design
from frontend.utils import (
    clear_active_case_id,
    get_active_case,
    get_user_id_for_jobs,
    set_active_case_id,
)


def create_navbar():
    """
    Create and render the main navigation bar component.

    This function generates a sticky navigation bar that appears at the top
    of every page. It includes the RescueBox branding and navigation links
    to major sections of the application.

    """
    # logger.info("Creating navigation bar component")

    with ui.header(wrap=False).classes(Design.NAV_HEADER):
        # logger.debug("Header created with sticky positioning and blue theme")

        _link_cls = Design.NAV_LINK
        _nav_locked = get_user_id_for_jobs() is None

        def _nav_blocked_msg():
            ui.notify(
                "Please select or create an active Case on the home page.",
                type="warning",
                classes="rb-notify-505759",
            )

        active_case = get_active_case()

        with ui.row().classes(
            "w-full min-w-0 min-h-12 h-auto sm:h-14 px-2 sm:px-3 py-0 items-center gap-2 sm:gap-3 "
            "box-border flex-wrap sm:flex-nowrap justify-start"
        ):
            # logger.debug("Creating navbar container with responsive layout")

            with ui.row().classes("shrink-0 items-center gap-2 min-w-0"):
                with ui.row().classes("items-center cursor-pointer").on(
                    "click", lambda _: ui.navigate.to("/")
                ):
                    ui.html(
                        '<img src="/icons/logo.png" class="h-8 sm:h-9 md:h-10 w-auto object-contain shrink-0" />',
                        sanitize=False,
                    )
                if active_case:
                    try:
                        all_cases = get_case_db().get_all_cases_sync()
                        other_cases = [
                            c for c in all_cases if c.caseId != active_case.caseId
                        ]
                    except UI_RENDER_ERRORS:
                        all_cases = [active_case]
                        other_cases = []

                    if len(all_cases) <= 1:
                        # Just show a clean static badge if there is only one case in the system
                        with ui.row().classes(
                            "items-center gap-1 bg-black/20 px-2.5 py-1 rounded-lg "
                            "border border-white/20 ml-2 cursor-pointer"
                        ).on("click", lambda _: ui.navigate.to("/case")):
                            ui.label(f"Case: {active_case.caseNumber}").classes(
                                "text-xs font-semibold text-white"
                            )
                    else:
                        # Show the interactive dropdown if there are multiple cases to switch between
                        with ui.dropdown_button(
                            f"Case: {active_case.caseNumber}",
                            color=None,
                            auto_close=True,
                        ).classes(
                            "text-xs font-semibold text-white bg-black/20 px-2.5 py-1 "
                            "rounded-lg border border-white/20 ml-2 cursor-pointer"
                        ).props(
                            "flat dense no-caps split"
                        ).on(
                            "click", lambda _: ui.navigate.to("/case")
                        ):
                            ui.menu_item(
                                "Case Overview",
                                on_click=lambda: ui.navigate.to("/case"),
                            ).classes("font-semibold text-[#881c1c]")
                            ui.separator()
                            if other_cases:
                                ui.label("Switch Case:").classes(
                                    "text-[10px] font-bold text-slate-400 px-3 py-1 uppercase tracking-wider"
                                )
                                for c in other_cases[:5]:  # Show up to 5 other cases

                                    def _switch_case(
                                        cid=c.caseId, case_number=c.caseNumber
                                    ):
                                        set_active_case_id(cid)
                                        ui.notify(
                                            f"Switched to case {case_number}.",
                                            type="positive",
                                        )
                                        ui.timer(
                                            0.3,
                                            lambda: ui.navigate.to("/case"),
                                            once=True,
                                        )

                                    ui.menu_item(c.caseNumber, on_click=_switch_case)
                                ui.separator()

                            def _close_active_case():
                                clear_active_case_id()
                                ui.notify("Case closed.", type="info")
                                ui.timer(0.2, lambda: ui.navigate.to("/"), once=True)

                            ui.menu_item(
                                "Close Case", on_click=_close_active_case
                            ).classes("text-rose-500 font-semibold")

            with ui.row().classes("min-w-0 flex-1 justify-end items-center"):
                with ui.row().classes(
                    "inline-flex flex-wrap items-center justify-end gap-x-0.5 gap-y-0 "
                    "max-w-full py-0"
                ):
                    # logger.debug("Creating navigation links row")

                    _nav_items = (
                        ("Assistant", "/chatbot"),
                        ("Jobs", "/jobs"),
                        ("Logs", "/logs"),
                    )
                    for label, path in _nav_items:
                        if _nav_locked:
                            ui.label(label).classes(
                                _link_cls + " opacity-50 cursor-not-allowed select-none"
                            ).on("click", lambda _: _nav_blocked_msg())
                        else:
                            ui.link(label, path).classes(_link_cls)

                    def _open_about() -> None:
                        ui.navigate.to(constants.NAV_LINKS["about"])

                    def _open_readme() -> None:
                        if _nav_locked:
                            _nav_blocked_msg()
                        else:
                            ui.navigate.to("/models")

                    def _open_demo() -> None:
                        ui.navigate.to("/demo")

                    with ui.dropdown_button(
                        "Resources",
                        color=None,
                        auto_close=True,
                    ).classes(_link_cls).props("flat dense no-caps"):
                        ui.menu_item("Readme", on_click=_open_readme)
                        ui.menu_item("About", on_click=_open_about)

                # Session display removed for demo safety (avoids accidental user actions)

                # Clear Session button removed to avoid accidental data loss
