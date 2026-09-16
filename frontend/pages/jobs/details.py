import logging

import httpx
from nicegui import ui

from frontend.components.chat import UIOperations
from frontend.components.jobs import (
    render_job_details_panel,
    render_job_outputs_card,
    render_pipeline_run_banner,
)
from frontend.components.shared import (
    create_breadcrumbs,
    render_page_header,
)
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.database import get_job_db
from frontend.job_progress import mirror_progress_to_jobs_db
from frontend.pages.page_shell import begin_demo_session_page
from frontend.utils.storage import get_user_id_for_jobs

from .utils import extract_job_fields

logger = logging.getLogger(__name__)


async def _maybe_render_pipeline_stepper(job_fields: dict) -> None:
    uid = job_fields.get("uid")
    root = job_fields.get("pipelineRootJobId") or uid
    try:
        user_id = get_user_id_for_jobs()
        if not user_id:
            return
        siblings = await get_job_db().list_jobs_for_pipeline_root(user_id, root)
        if len(siblings) < 2:
            return
        steps = [{"job_id": s.uid, "endpoint": s.endpoint or ""} for s in siblings]
        render_pipeline_run_banner(
            root_job_id=siblings[0].uid if siblings else root,
            current_job_id=uid,
            steps=steps,
        )
    except UI_RENDER_ERRORS as e:
        logger.debug("Pipeline stepper failed: %s", e)


@ui.page("/jobs/{job_id}")
async def job_details_page_route(job_id: str):
    if not begin_demo_session_page():
        return

    try:
        job = await get_job_db().get_job_by_uid(job_id)
        if job and str(job.status) == "Running":
            await mirror_progress_to_jobs_db(job_id)
            job = await get_job_db().get_job_by_uid(job_id)
        if not job:
            ui.label(f"Job not found: {job_id}").classes("text-red-600")
            return
    except UI_RENDER_ERRORS as e:
        logger.error("Error loading job %s: %s", job_id, e)
        ui.label(f"Error loading job: {e!s}").classes("text-red-600")
        return

    jf = extract_job_fields(job)

    # Auto-refresh if the job is running or pending
    status = str(jf.get("status", "")).lower()
    if status in ("running", "pending"):

        def _reload_job_page() -> None:
            ui.navigate.reload()

        ui.timer(3.0, _reload_job_page, once=True)

    with ui.column().classes(
        "container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16 items-stretch"
    ):
        create_breadcrumbs(
            [{"label": "Jobs", "link": "/jobs"}, {"label": f"Job {job_id}"}]
        )
        await _maybe_render_pipeline_stepper(jf)

        render_page_header("Job Results")

        with ui.tabs().classes("w-full mb-4") as tabs:
            ui.tab("Outputs")
            ui.tab("Details")

        open_details = str(jf.get("status")) == "Failed" and not jf.get("response")
        tab_panels = ui.tab_panels(
            tabs, value="Details" if open_details else "Outputs"
        ).classes("w-full")

        api_c = httpx.AsyncClient()
        with tab_panels:
            with ui.tab_panel("Outputs"):
                try:
                    await render_job_outputs_card(
                        ui.column().classes("w-full"), api_c, job
                    )
                except UI_RENDER_ERRORS as e:
                    logger.exception("Failed to render Outputs tab: %s", e)
                    ui.label(f"Error rendering outputs: {e}").classes("text-red-600")
            with ui.tab_panel("Details"):
                try:
                    await render_job_details_panel(
                        ui.column().classes("w-full"), api_c, jf
                    )
                except UI_RENDER_ERRORS as e:
                    logger.exception("Failed to render Details tab: %s", e)
                    ui.label(f"Error rendering details: {e}").classes("text-red-600")

        UIOperations.scroll_document_to_bottom()
