"""Case management dashboard sections for the home page."""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.database import get_case_db
from frontend.design_tokens import Design
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.utils import (
    browse_directory_simple,
    set_active_case_id,
)

logger = logging.getLogger(__name__)

_LOAD_CASE_CARD = (
    "w-full p-4 border-l-4 border-l-[#881c1c] border-y border-r border-slate-200 "
    "hover:border-slate-300 hover:shadow-md transition-all bg-slate-50 rounded-xl"
)


async def render_case_management_cards() -> None:
    """Create-new and load-existing case cards on the home dashboard."""
    with ui.row().classes("w-full gap-8 items-stretch flex-wrap md:flex-nowrap"):
        _render_create_case_card()
        await _render_load_existing_cases_card()


def _render_create_case_card() -> None:
    with ui.card().classes(
        "flex-1 p-6 border-t-4 border-t-[#881c1c] border-x border-b "
        "border-slate-200 shadow-md rounded-2xl bg-white"
    ):
        with ui.row().classes("items-center gap-2 mb-4"):
            ui.label("Create New Case").classes("text-2xl font-bold text-slate-800")

        case_num_input = (
            ui.input(
                "Case Number / ID (Required, Unique)",
                placeholder="e.g., CASE-2026-0042",
            )
            .classes("w-full mb-4")
            .props("outlined dense")
        )

        investigators_input = (
            ui.input(
                "Investigators",
                placeholder="e.g., Det. Smith, Agent Jones",
            )
            .classes("w-full mb-4")
            .props("outlined dense")
        )

        with ui.column().classes("w-full mb-6 gap-1"):
            ui.label("Evidence Directory / UFDR Path").classes(
                "text-sm font-medium text-slate-700"
            )
            with ui.row().classes("w-full items-center gap-2 flex-nowrap"):
                path_input = (
                    ui.input(placeholder="/path/to/evidence")
                    .classes("flex-1")
                    .props("outlined dense")
                )

                ui.button(
                    "Browse",
                    color=None,
                    on_click=lambda: browse_directory_simple(path_input),
                ).classes(Design.BTN_MEDIUM_GRAY)

        async def _on_create():
            await _create_case(case_num_input, investigators_input, path_input)

        ui.button(
            "Create & Load Case",
            color=None,
            on_click=_on_create,
        ).classes(Design.BTN_PRIMARY + " w-full py-3 text-base")


async def _create_case(case_num_input, investigators_input, path_input) -> None:
    num = (case_num_input.value or "").strip()
    inv = (investigators_input.value or "").strip()
    path = (path_input.value or "").strip()

    if not num:
        ui.notify("Case Number is required.", type="warning")
        return
    if not path:
        ui.notify("Evidence Path is required.", type="warning")
        return

    try:
        case_db = get_case_db()
        new_case = await case_db.create_case(
            case_number=num,
            investigators=inv,
            evidence_path=path,
        )
        set_active_case_id(new_case.caseId)
        ui.notify(f"Case {num} created and loaded successfully.", type="positive")

        def _go_case() -> None:
            ui.navigate.to("/case")

        ui.timer(0.5, _go_case, once=True)
    except ValueError as e:
        ui.notify(str(e), type="negative")
    except UI_RENDER_ERRORS as e:
        ui.notify(f"Failed to create case: {e}", type="negative")


async def _render_load_existing_cases_card() -> None:
    with ui.card().classes(
        "flex-1 p-6 border-t-4 border-t-[#881c1c] border-x border-b "
        "border-slate-200 shadow-md rounded-2xl bg-white flex flex-col"
    ):
        with ui.row().classes("items-center gap-2 mb-4"):
            ui.label("Load Existing Case").classes("text-2xl font-bold text-slate-800")

        cases_container = ui.column().classes(
            "w-full flex-1 overflow-y-auto space-y-3 max-h-[400px]"
        )
        await _populate_cases_list(cases_container)


async def _populate_cases_list(cases_container) -> None:
    cases_container.clear()
    try:
        case_db = get_case_db()
        all_cases = await case_db.get_all_cases()
        if not all_cases:
            with cases_container:
                ui.label("No existing cases found.").classes(
                    "text-slate-400 italic p-4 text-center w-full"
                )
            return

        with cases_container:
            for c in all_cases:
                _render_case_row(c)
    except UI_RENDER_ERRORS as e:
        logger.error("Error loading cases: %s", e)
        with cases_container:
            ui.label(f"Error loading cases: {e}").classes("text-red-500")


def _render_case_row(case) -> None:
    with ui.card().classes(_LOAD_CASE_CARD):
        with ui.row().classes("w-full justify-between items-center"):
            with ui.column().classes("gap-1 flex-1 min-w-0"):
                with ui.row().classes("items-center gap-1.5"):
                    ui.label(case.caseNumber).classes(
                        "font-bold text-lg text-slate-800 truncate"
                    )
                if case.investigators:
                    with ui.row().classes("items-center gap-1.5"):
                        ui.label(f"Investigators: {case.investigators}").classes(
                            "text-sm text-slate-600 truncate"
                        )
                with ui.row().classes("items-center gap-1.5"):
                    ui.label(f"Path: {case.evidencePath}").classes(
                        "text-xs font-mono text-slate-500 truncate"
                    )

            def _load(cid=case.caseId, cnum=case.caseNumber):
                set_active_case_id(cid)
                ui.notify(f"Loaded case {cnum}.", type="positive")

                def _go_case() -> None:
                    ui.navigate.to("/case")

                ui.timer(0.3, _go_case, once=True)

            ui.button(
                "Load",
                color=None,
                on_click=_load,
            ).classes(Design.BTN_PRIMARY_COMPACT)
