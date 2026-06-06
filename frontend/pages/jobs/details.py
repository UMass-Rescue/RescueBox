import logging
import httpx
from nicegui import ui
from frontend.components.shared import create_navbar, create_breadcrumbs
from frontend.database import get_job_db
from frontend.components.chat import UIOperations
from frontend.utils import apply_saved_theme, require_demo_user_session
from .utils import extract_job_fields

logger = logging.getLogger(__name__)


async def _maybe_render_pipeline_stepper(job_fields: dict) -> None:
    uid = job_fields.get("uid")
    root = job_fields.get("pipelineRootJobId") or uid
    try:
        from frontend.utils import get_user_id_for_jobs

        user_id = get_user_id_for_jobs()
        if not user_id:
            return
        siblings = await get_job_db().list_jobs_for_pipeline_root(user_id, root)
        if len(siblings) < 2:
            return
        from frontend.components.jobs import render_pipeline_run_banner

        steps = [{"job_id": s.uid, "endpoint": s.endpoint or ""} for s in siblings]
        render_pipeline_run_banner(
            root_job_id=siblings[0].uid if siblings else root,
            current_job_id=uid,
            steps=steps,
        )
    except Exception as e:
        logger.debug("Pipeline stepper failed: %s", e)


@ui.page("/jobs/{job_id}")
async def job_details_page_route(job_id: str):
    apply_saved_theme()
    create_navbar()
    if not require_demo_user_session():
        return

    try:
        job = await get_job_db().get_job_by_uid(job_id)
        if not job:
            ui.label(f"Job not found: {job_id}").classes("text-red-600")
            return
    except Exception as e:
        logger.error("Error loading job %s: %s", job_id, e)
        ui.label(f"Error loading job: {str(e)}").classes("text-red-600")
        return

    jf = extract_job_fields(job)

    # Auto-refresh if the job is running or pending
    status = str(jf.get("status", "")).lower()
    if status in ("running", "pending"):
        ui.timer(3.0, lambda: ui.navigate.reload(), once=True)

    with ui.column().classes(
        "container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16 items-stretch"
    ):
        create_breadcrumbs(
            [{"label": "Jobs", "link": "/jobs"}, {"label": f"Job {job_id}"}]
        )
        await _maybe_render_pipeline_stepper(jf)

        from frontend.components.shared import render_page_header

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
                    from frontend.components.jobs import render_job_outputs_card

                    await render_job_outputs_card(
                        ui.column().classes("w-full"), api_c, job
                    )
                except Exception as e:
                    logger.exception("Failed to render Outputs tab: %s", e)
                    ui.label(f"Error rendering outputs: {e}").classes("text-red-600")
            with ui.tab_panel("Details"):
                try:
                    from frontend.components.jobs import render_job_details_panel

                    await render_job_details_panel(
                        ui.column().classes("w-full"), api_c, jf
                    )
                except Exception as e:
                    logger.exception("Failed to render Details tab: %s", e)
                    ui.label(f"Error rendering details: {e}").classes("text-red-600")

        UIOperations.scroll_document_to_bottom()
