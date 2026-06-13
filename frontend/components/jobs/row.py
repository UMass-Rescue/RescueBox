"""Job table row UI (status, timestamps, actions)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable, Dict, Optional

from nicegui import ui

from frontend.design_tokens import Design
from frontend.components.jobs.status_badge import append_job_status_icon_and_label
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)

_ROW_CANCEL_BTN = (
    "bg-rose-50 hover:bg-rose-100 text-rose-700 px-3 py-1 rounded text-sm "
    "transition-colors border border-rose-200"
)
_ROW_DELETE_BTN = (
    "bg-rose-50 hover:bg-rose-100 text-[#881c1c] px-3 py-1 rounded text-sm "
    "transition-colors border border-rose-200"
)


def render_job_row(
    container,
    job: Dict,
    plugin_name: Optional[str] = None,
    on_view: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
):
    """
    Render a job row in table format.

    This function creates a table row component displaying job information including
    model name, status, timestamps, and action buttons. The row uses color-coding
    to indicate job status (Running, Completed, Failed, Canceled).

    """
    logger.debug(
        "Rendering job row for job: %s (Status: %s)",
        job.get("uid", "Unknown"),
        job.get("status", "Unknown"),
    )

    status = job.get("status", "Unknown")

    # Status Pill Badges
    status_pill_classes = {
        "Completed": "bg-emerald-50 text-emerald-700 border border-emerald-200",
        "Running": "bg-rose-50 text-[#881c1c] border border-rose-200",
        "Failed": "bg-rose-50 text-rose-700 border border-rose-200",
        "Canceled": "bg-slate-100 text-slate-600 border border-slate-200",
    }
    pill_cls = status_pill_classes.get(
        status, "bg-slate-50 text-slate-500 border border-slate-200"
    )

    # Format timestamps
    start_time_str = "N/A"
    if job.get("startTime"):
        try:
            start_time = datetime.fromisoformat(job["startTime"].replace("Z", "+00:00"))
            start_time_str = start_time.strftime("%Y-%m-%d %H:%M")
        except UI_RENDER_ERRORS as e:
            logger.warning(
                "Failed to parse start time: %s, error: %s", job["startTime"], e
            )
            start_time_str = job["startTime"]

    end_time_str = "N/A"
    if job.get("endTime"):
        try:
            end_time = datetime.fromisoformat(job["endTime"].replace("Z", "+00:00"))
            end_time_str = end_time.strftime("%Y-%m-%d %H:%M")
        except UI_RENDER_ERRORS as e:
            logger.warning("Failed to parse end time: %s, error: %s", job["endTime"], e)
            end_time_str = job["endTime"]

    job_uid = job.get("uid", "N/A")
    with container:
        with ui.row().classes(
            "p-4 border-b border-slate-200 hover:bg-slate-50 items-center w-full flex-nowrap gap-2 bg-white"
        ):
            # Job ID - truncated with ellipsis, full ID on hover
            with ui.element("div").classes("w-40 min-w-0 shrink-0"):
                id_label = ui.label(job_uid).classes(
                    "font-mono text-sm truncate block text-slate-800"
                )
                id_label.tooltip(job_uid)

            # Model name (and notes indicator)
            with ui.element("div").classes(
                "flex-1 min-w-0 overflow-hidden flex items-center gap-2 text-slate-800"
            ):
                ui.label(plugin_name or "Unknown").classes("truncate block font-medium")
                if job.get("caseNotes"):
                    notes_preview = (job["caseNotes"] or "")[:50]
                    if len(job.get("caseNotes", "") or "") > 50:
                        notes_preview += "…"
                    ui.icon("description", size="sm").classes(
                        "text-slate-500 shrink-0"
                    ).tooltip(notes_preview)

            # Times (start / end)
            with ui.column().classes("w-64 shrink-0 gap-0.5"):
                ui.label(start_time_str).classes("text-sm text-slate-700")
                ui.label(
                    f"Ended: {end_time_str}" if end_time_str != "N/A" else "Active"
                ).classes("text-xs text-slate-500")

            # Status Pill Badge
            with ui.row().classes(
                f"w-32 shrink-0 items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold {pill_cls}"
            ):
                append_job_status_icon_and_label(status)

            # Actions
            with ui.row().classes("gap-2 w-48 shrink-0 flex-nowrap"):
                if on_view:
                    ui.button(
                        "View",
                        color=None,
                        on_click=lambda: on_view(job["uid"]) if on_view else None,
                    ).classes(Design.BTN_PRIMARY_TIGHT)

                if status == "Running" and on_cancel:
                    ui.button(
                        "Cancel",
                        color=None,
                        on_click=lambda: on_cancel(job["uid"]) if on_cancel else None,
                    ).classes(_ROW_CANCEL_BTN)
                elif status != "Running" and on_delete:
                    ui.button(
                        "Delete",
                        color=None,
                        on_click=lambda: on_delete(job["uid"]) if on_delete else None,
                    ).classes(_ROW_DELETE_BTN)
                    # logger.debug("Delete button added")
