"""Active case overview UI for the ``/case`` route."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from nicegui import ui

from frontend.components.jobs.status_badge import append_job_status_icon_and_label
from frontend.database import get_case_db, get_job_db
from frontend.design_tokens import Design
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.utils import clear_active_case_id

logger = logging.getLogger(__name__)

_PAGE_COLUMN_CLASSES = (
    "container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16 gap-8"
)
_CASE_INFO_CARD_CLASSES = (
    "w-full p-6 border-t-4 border-t-[#881c1c] border-x border-b border-slate-200 "
    "shadow-md rounded-2xl bg-white mb-8"
)
_CASE_ID_VALUE_CLASSES = (
    "font-mono text-slate-600 truncate bg-slate-50 px-2 py-0.5 rounded "
    "border border-slate-100"
)
_CHANGE_PATH_DIALOG_CARD = (
    "p-6 w-full max-w-lg bg-white border-t-4 border-t-[#881c1c] border-x border-b "
    "border-slate-200 rounded-2xl shadow-xl"
)
_NO_JOBS_LABEL_CLASSES = (
    "text-slate-400 italic p-6 text-center w-full bg-slate-50 rounded-xl "
    "border border-dashed border-slate-200"
)
_REMOVE_JOB_BTN_CLASSES = (
    "bg-rose-50 hover:bg-rose-100 text-[#881c1c] px-3 py-1 rounded text-sm "
    "transition-colors border border-rose-200"
)

_STATUS_PILL_CLASSES = {
    "Completed": "bg-emerald-50 text-emerald-700 border border-emerald-200",
    "Running": "bg-rose-50 text-[#881c1c] border border-rose-200",
    "Failed": "bg-rose-50 text-rose-700 border border-rose-200",
    "Canceled": "bg-slate-100 text-slate-600 border border-slate-200",
}
_DEFAULT_STATUS_PILL = "bg-slate-50 text-slate-500 border border-slate-200"


def _navigate_home() -> None:
    ui.navigate.to("/")


def _reload_case_page() -> None:
    ui.navigate.reload()


def _open_job_page(job_id: str) -> Callable[[], None]:
    def _go() -> None:
        ui.navigate.to(f"/jobs/{job_id}")

    return _go


async def render_active_case_overview(active_case_id: str) -> None:
    """Render case details and associated jobs when a case is active."""
    with ui.column().classes(_PAGE_COLUMN_CLASSES):
        case_db = get_case_db()
        case = await case_db.get_case_by_id(active_case_id)
        if not case:
            clear_active_case_id()
            ui.timer(0.1, _navigate_home, once=True)
            return

        with ui.row().classes("items-center gap-3 mb-2"):
            ui.label(f"Case: {case.caseNumber}").classes(
                "text-4xl font-bold text-slate-800"
            )
        if case.investigators:
            with ui.row().classes("items-center gap-2 mb-6 pl-1"):
                ui.label(f"Investigators: {case.investigators}").classes(
                    "text-lg text-slate-600"
                )

        with ui.card().classes(_CASE_INFO_CARD_CLASSES):
            with ui.row().classes(
                "items-center gap-2 mb-4 border-b pb-2 border-slate-100"
            ):
                ui.label("Case Information").classes("text-xl font-bold text-slate-800")
            with ui.column().classes("w-full gap-3"):
                with ui.row().classes("items-center gap-2.5"):
                    ui.label("Case ID:").classes(
                        "font-semibold text-slate-700 w-24 shrink-0"
                    )
                    ui.label(case.caseId).classes(_CASE_ID_VALUE_CLASSES)
                with ui.row().classes("items-center gap-2.5"):
                    ui.label("Created:").classes(
                        "font-semibold text-slate-700 w-24 shrink-0"
                    )
                    ui.label(case.createdAt[:10] + " " + case.createdAt[11:16]).classes(
                        "text-slate-600"
                    )
                with ui.row().classes(
                    "items-center gap-2.5 w-full flex-wrap sm:flex-nowrap"
                ):
                    ui.label("Evidence Path:").classes(
                        "font-semibold text-slate-700 w-24 shrink-0"
                    )
                    path_display = (
                        ui.input(value=case.evidencePath)
                        .classes("flex-1 min-w-0")
                        .props("outlined dense readonly")
                    )
                    with path_display.add_slot("prepend"):
                        ui.icon("folder", size="xs").classes("text-slate-400")

                    async def _change_path():
                        with ui.dialog() as d, ui.card().classes(
                            _CHANGE_PATH_DIALOG_CARD
                        ):
                            with ui.row().classes("items-center gap-2 mb-4"):
                                ui.label("Update Evidence Path").classes(
                                    "text-xl font-bold text-slate-800"
                                )
                            new_path_input = (
                                ui.input(
                                    "New Evidence Directory / UFDR Path",
                                    value=case.evidencePath,
                                )
                                .classes("w-full mb-6")
                                .props("outlined dense")
                            )
                            with new_path_input.add_slot("prepend"):
                                ui.icon("folder").classes("text-slate-400")
                            with ui.row().classes("w-full justify-end gap-2"):
                                ui.button(
                                    "Cancel", color=None, on_click=d.close
                                ).classes(Design.BTN_MEDIUM_GRAY)

                                async def _save_path():
                                    p = (new_path_input.value or "").strip()
                                    if not p:
                                        ui.notify(
                                            "Path cannot be empty.", type="warning"
                                        )
                                        return
                                    await case_db.update_case_evidence_path(
                                        case.caseId, p
                                    )
                                    ui.notify(
                                        "Evidence path updated successfully.",
                                        type="positive",
                                    )
                                    d.close()
                                    ui.timer(0.3, _reload_case_page, once=True)

                                ui.button(
                                    "Save", color=None, on_click=_save_path
                                ).classes(Design.BTN_PRIMARY_COMPACT)
                        d.open()

                    ui.button("Change Path", color=None, on_click=_change_path).classes(
                        Design.BTN_MEDIUM_GRAY
                    )

        with ui.row().classes("items-center gap-2 mb-4"):
            ui.label("Case Results & Jobs").classes("text-2xl font-bold text-slate-800")

        jobs_container = ui.column().classes("w-full space-y-2")

        async def _load_case_jobs():
            jobs_container.clear()
            try:
                job_db = get_job_db()
                jobs_data = await job_db.get_all_jobs()
                if not jobs_data:
                    with jobs_container:
                        ui.label("click on Assistant to run a new job.").classes(
                            _NO_JOBS_LABEL_CLASSES
                        )
                    return

                with jobs_container:
                    with ui.row().classes(
                        "bg-[#1c1c1c] text-white p-4 font-semibold w-full rounded-t-xl "
                        "items-center"
                    ):
                        ui.label("Job ID").classes("w-32 shrink-0")
                        ui.label("Plugin / Task").classes("flex-1 min-w-0")
                        ui.label("Start Time").classes("w-48 shrink-0")
                        ui.label("Status").classes("w-36 shrink-0")
                        ui.label("Actions").classes("w-48 shrink-0")

                    for job in jobs_data:
                        _render_case_job_row(job, _load_case_jobs)

            except UI_RENDER_ERRORS as e:
                logger.error("Error loading case jobs: %s", e)
                with jobs_container:
                    ui.label(f"Error loading jobs: {e}").classes("text-red-500")

        await _load_case_jobs()


def _render_case_job_row(
    job: dict,
    reload_jobs: Callable[[], Awaitable[None]],
) -> None:
    uid = job.get("uid")
    endpoint = job.get("endpoint")
    pname = job.get("plugin_name") or endpoint or "Unknown"
    start_time = job.get("startTime") or "N/A"
    if "T" in start_time:
        start_time = start_time.replace("T", " ")[:16]
    status = job.get("status", "Unknown")

    pill_cls = _STATUS_PILL_CLASSES.get(status, _DEFAULT_STATUS_PILL)

    with ui.row().classes(
        "p-4 border-b border-slate-200 hover:bg-slate-50 items-center w-full "
        "flex-nowrap gap-2 bg-white"
    ):
        ui.label(uid).classes(
            "font-mono text-sm w-32 shrink-0 truncate text-slate-800"
        ).tooltip(uid)
        ui.label(pname).classes("flex-1 min-w-0 truncate text-slate-800")
        ui.label(start_time).classes("w-48 shrink-0 text-sm text-slate-600")

        with ui.row().classes(
            f"w-36 shrink-0 items-center gap-1.5 px-2.5 py-1 rounded-full "
            f"text-xs font-semibold {pill_cls}"
        ):
            append_job_status_icon_and_label(status)

        with ui.row().classes("w-48 shrink-0 gap-2 flex-nowrap"):
            ui.button(
                "View",
                color=None,
                on_click=_open_job_page(uid),
            ).classes(Design.BTN_PRIMARY_TIGHT)

            async def _remove_job():
                await get_job_db().disassociate_job_from_case(uid)
                ui.notify(f"Job {uid} removed from case.", type="info")
                await reload_jobs()

            ui.button(
                "Delete",
                color=None,
                on_click=_remove_job,
            ).classes(_REMOVE_JOB_BTN_CLASSES)
