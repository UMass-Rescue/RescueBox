"""Shared job status pill (icon + label) for jobs list and case overview."""

from __future__ import annotations

from nicegui import ui


def append_job_status_icon_and_label(status: str) -> None:
    """Add status icon and label inside the caller's ``ui.row`` context."""
    if status == "Completed":
        ui.icon("check_circle", size="14px")
    elif status == "Running":
        ui.spinner(size="14px").classes("text-[#881c1c]")
    elif status == "Failed":
        ui.icon("error", size="14px")
    else:
        ui.icon("cancel", size="14px")
    ui.label(status)
