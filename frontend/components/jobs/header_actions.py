from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from nicegui import ui

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.database.job_field_utils import get_plugin_name

logger = logging.getLogger(__name__)


def render_jobs_header(
    container: ui.element, title: str, _on_refresh: Callable | None = None
):
    """
    Render the jobs page header with title and refresh button.
    """
    try:
        with container, ui.row().classes("items-center justify-between mb-6"):
            ui.label(title).classes("text-4xl font-bold")
    except UI_RENDER_ERRORS as e:
        logger.exception("Failed to render jobs header component: %s", e)


def render_job_action_buttons(job_fields: dict[str, Any]) -> None:
    model_uid = job_fields.get("modelUid")
    with ui.row().classes("gap-2"):
        if model_uid:
            ui.button(
                "Model Doc",
                color=None,
                on_click=lambda: ui.navigate.to(f"/models/{model_uid}/details"),
            ).classes("rb-brand-primary text-white")
            ui.button(
                "Run Model",
                color=None,
                on_click=lambda: ui.navigate.to(f"/models/{model_uid}/run"),
            ).classes("rb-brand-primary text-white rounded-xl")


def render_error_status(status: str, status_text: str | None = None) -> None:
    with ui.card().classes(
        "bg-rose-50 border border-rose-200 p-6 rounded-2xl shadow-sm border-t-4 border-t-rose-500"
    ):
        with ui.row().classes("items-center gap-2 mb-2"):
            ui.icon("error", size="md").classes("text-rose-600")
            ui.label("Job Failed").classes("text-2xl font-bold text-rose-800")
        ui.label(f"Status: {status}").classes("text-lg text-rose-700 font-medium")
        if status_text:
            ui.label(status_text).classes(
                "text-sm text-rose-600 mt-2 bg-white/50 p-3 rounded-lg border border-rose-100 whitespace-pre-wrap"
            )


def render_running_status(status_text: str | None = None) -> None:
    detail = (status_text or "").strip() or "Running"
    with ui.card().classes(
        "bg-rose-50 border border-rose-200 p-6 rounded-2xl shadow-sm border-t-4 border-t-[#881c1c]"
    ):
        with ui.row().classes("items-center gap-2 mb-2"):
            ui.spinner(size="md").classes("text-[#881c1c]")
            ui.label("Job in progress").classes("text-2xl font-bold text-[#881c1c]")
        ui.label(detail).classes("text-lg text-rose-800 font-medium")


def render_job_metadata(job_fields: dict[str, Any]) -> None:
    with ui.column().classes("gap-2 mt-4"):
        ui.label("Job ID:").classes("font-semibold")
        ui.label(job_fields.get("uid", "Unknown")).classes("text-sm text-zinc-600 mb-2")


async def render_model_info(api_client, job_fields: dict[str, Any]) -> None:
    model_uid = job_fields.get("modelUid")
    if not model_uid:
        return
    try:
        name = await get_plugin_name(api_client, model_uid) or model_uid
        with ui.column().classes("gap-1 mt-4"):
            ui.label("Plugin / Model").classes("font-semibold")
            with ui.row().classes("items-center gap-2"):
                ui.label(name).classes("text-sm text-zinc-800")
                ui.label(f"({model_uid})").classes("text-xs text-zinc-500 font-mono")
    except UI_RENDER_ERRORS as e:
        logger.debug("Failed to render model info: %s", e)


def render_job_actions(container: ui.element, job_fields: dict[str, Any]) -> None:
    """
    Render job action buttons into the provided container.
    Delegates to the existing job actions implementation with a safe fallback.
    """
    try:
        with container:
            render_job_action_buttons(job_fields)
    except UI_RENDER_ERRORS as e:
        logger.exception("Failed to render job actions via component: %s", e)
